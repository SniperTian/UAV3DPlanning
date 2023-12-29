// region选择区域
function chooseArea(){
    // 重置区域显示状态
    $("input#showArea").prop("checked", "true");
    // 清除旧选区
    if(globalThis.photoArea!=null){
        globalThis.photoArea.destroy();
    }
    // 用全局变量link绘制的航摄区域
    var mouseTool = new AMap.MouseTool(map)
    mouseTool.on('draw',function(event){
        // event.obj 为绘制出来的覆盖物对象
        globalThis.photoArea = event.obj;
        //log.info(photoArea.getOptions().bounds)
        mouseTool.close()
        log.info('航摄区域选择完成')
        //log.info(photoArea.getOptions())
    })
    // 绘制新选区
    mouseTool.rectangle({
        zIndex:9,
        strokeColor:'red',
        strokeOpacity:0.5,
        strokeWeight: 6,
        fillColor:'blue',
        fillOpacity:0.5,
        // strokeStyle还支持 solid
        strokeStyle: 'solid',
        // strokeDasharray: [30,10],
    })
}
function showArea(){
    if(globalThis.photoArea!=null){
        globalThis.photoArea.show();
    }
}
function hideArea(){
    if(globalThis.photoArea!=null){
        globalThis.photoArea.hide();
    }
}
// endregion选择区域
// region显示建筑模型
function loadBuildings(){
    // 重置图层显示状态
    $("input#showBuildings").prop("checked", "true");
    // 删除旧图层
    if(globalThis.buildingLayer!=null){
        globalThis.map.remove(globalThis.buildingLayer)
        globalThis.buildingLayer = null
    }
    // 获取选区范围
    var areaBounds = globalThis.photoArea.getOptions().bounds
    buildingList = getBuildings(areaBounds)

    // 绘制建筑3D图层
    drawBuildings(buildingList)
}
function getBuildings(areaBounds){
    var sw = areaBounds.getSouthWest() //SouthWest
    var ne = areaBounds.getNorthEast() //NorthEast
    //window.alert(sw)
    //window.alert(ne)
    // 选区边界坐标转换 gcj02 -> wgs84
    var sw_wgs84 = coordtransform.gcj02towgs84(sw.getLng(),sw.getLat())
    var ne_wgs84 = coordtransform.gcj02towgs84(ne.getLng(),ne.getLat())
    //window.alert(sw_wgs84)
    //window.alert(ne_wgs84)
    var upload_data = {
        "area_bounds" : [sw_wgs84[0],sw_wgs84[1],ne_wgs84[0],ne_wgs84[1]],
        "area_bounds_name": ["sw_lng","sw_lat","ne_lng","ne_lat",],
    }
    var getBuildings_url = "/routeplan3d/get-buildings"
    var buildingList_wgs84;
    $.ajax({
        async:false,
        url: getBuildings_url,
        type: "POST",
        dateType:'json',
        data: upload_data,
        headers:{
            "X-CSRFtoken":$.cookie("csrftoken"),
        },
        success:function (data) {
            log.info("成功获取建筑信息")
            buildingList_wgs84 = data["building_list"]
        }
    })
    // 建筑坐标转换 wgs84 -> gcj02
    //window.alert(buildingList_wgs84[0]["polygonExterior_wgs84"])
    var buildingList_gcj02 = []
    for(var i = 0; i < buildingList_wgs84.length; ++i){
        var building_wgs84 = buildingList_wgs84[i];
        var polygonExterior_wgs84 = building_wgs84["polygonExterior_wgs84"];
        var polygonExterior_gcj02 = [];
        for(var j = 0; j < polygonExterior_wgs84.length; ++j){
            lnglat_wgs84 = polygonExterior_wgs84[j]
            lnglat_gcj02 = coordtransform.wgs84togcj02(lnglat_wgs84[0], lnglat_wgs84[1])
            polygonExterior_gcj02[j] = lnglat_gcj02
        };
        buildingList_gcj02.push({
            "polygonExterior": polygonExterior_gcj02,
            "height": building_wgs84["height"],
        })
    }
    //window.alert(buildingList_gcj02[0]["polygonExterior"])
    return buildingList_gcj02
}
function drawBuildings(buildingList_gcj02){
    var camera;
    var renderer;
    var scene;
    var meshes = [];
    //region 数据转换:gcj02-map
    // 数据转换工具
    var customCoords = globalThis.map.customCoords;
    var buildingList_map = []
    //window.alert(buildingList_gcj02[0]["polygonExterior"])
    for(var i = 0; i < buildingList_gcj02.length; ++i){
        var building_gcj02 = buildingList_gcj02[i];
        var polygonExterior_gcj02 = building_gcj02["polygonExterior"]
        var polygonExterior_map = customCoords.lngLatsToCoords(polygonExterior_gcj02);
        //window.alert(customCoords.lngLatsToCoords(polygonExterior_gcj02))
        //window.alert(polygonExterior_map)
        buildingList_map.push({
            "polygonExterior":polygonExterior_map,
            "height": building_gcj02["height"],
        })
    }
    //endregion

    // region 创建 GL 图层
    var gllayer = new AMap.GLCustomLayer({
        // 图层的层级
        zIndex: 10,
        // 初始化的操作，创建图层过程中执行一次。
        init: (gl) => {
            //region 相机和场景设置
            // 这里我们的地图模式是 3D，所以创建一个透视相机，相机的参数初始化可以随意设置，因为在 render 函数中，每一帧都需要同步相机参数，因此这里变得不那么重要。
            // 如果你需要 2D 地图（viewMode: '2D'），那么你需要创建一个正交相机
            camera = new THREE.PerspectiveCamera(
                60,
                window.innerWidth / window.innerHeight,
                100,
                1 << 30
            );

            renderer = new THREE.WebGLRenderer({
                context: gl, // 地图的 gl 上下文
                // alpha: true,
                // antialias: true,
                // canvas: gl.canvas,
            });

            // 自动清空画布这里必须设置为 false，否则地图底图将无法显示
            renderer.autoClear = false;
            scene = new THREE.Scene();

            // 环境光照和平行光
            var aLight = new THREE.AmbientLight(0xffffff, 0.3);
            var dLight = new THREE.DirectionalLight(0xffffff, 1);
            dLight.position.set(1000, -100, 900);
            scene.add(dLight);
            scene.add(aLight);
            //endregion 相机和场景设置

            //region 绘制
            // 材质设定
            var bMaterial = new THREE.MeshPhongMaterial( { 
                color: 'wheat',
                //side: THREE.DoubleSide, 
                transparent: true,
                opacity: 0.5,
            } );
            // 几何体生成
            for(var i = 0; i < buildingList_map.length; ++i){
                var building = buildingList_map[i]
                var polygonExterior = building["polygonExterior"]
                var pLength = polygonExterior.length //外环点数
                var bHeight = building["height"] //建筑高度
                // 设置几何体顶点
                var polygonExterior3D = []
                // 初始化底部
                for(var j = 0; j < pLength; ++j){
                    point = polygonExterior[j]
                    polygonExterior3D.push(point[0],point[1],0)
                }
                // 初始化顶部
                for(var j = 0; j < pLength; ++j){ 
                    point = polygonExterior[j]
                    polygonExterior3D.push(point[0],point[1],bHeight)
                }
                // 设置几何体顶点链接顺序
                var polygonExterior3D_linkOrder = [] //顶点链接顺序
                for(var j = 0; j < pLength - 1; ++j){
                    polygonExterior3D_linkOrder.push(j,pLength+j,j+1)
                    polygonExterior3D_linkOrder.push(j+1,pLength+j,pLength+j+1)
                }
                polygonExterior3D_linkOrder.push(pLength-1,2*pLength-1,0)
                polygonExterior3D_linkOrder.push(0,2*pLength-1,pLength)
                // 生成建筑物侧面
                var bGeometry_side = new THREE.BufferGeometry() //几何体初始化
                var bVertices = new Float32Array(polygonExterior3D)
                var bIndices = new Uint16Array(polygonExterior3D_linkOrder)
                bGeometry_side.attributes.position = new THREE.BufferAttribute(bVertices, 3)
                bGeometry_side.index = new THREE.BufferAttribute(bIndices,1)
                var bMesh_side = new THREE.Mesh(bGeometry_side, bMaterial)
                // 生成建筑物顶部
                var bShape_Arr = []
                for(var j = 0; j< pLength; ++j){
                    point = polygonExterior[j]
                    bShape_Arr.push(
                        new THREE.Vector2(point[0],point[1]),
                    )
                }
                var bShape = new THREE.Shape(bShape_Arr)
                var bGeometry_top = new THREE.ShapeGeometry(bShape)
                bGeometry_top.translate(x = 0, y = 0, z = bHeight)
                var bMesh_top = new THREE.Mesh(bGeometry_top, bMaterial)
                //添加Mesh
                scene.add(bMesh_side)
                scene.add(bMesh_top)
            }
            //endregion
        },
        render: () => {
            // 这里必须执行！！重新设置 three 的 gl 上下文状态。
            renderer.resetState();
            // 重新设置图层的渲染中心点，将模型等物体的渲染中心点重置
            // 否则和 LOCA 可视化等多个图层能力使用的时候会出现物体位置偏移的问题
            //customCoords.setCenter([116.29932,39.98456]);
            var { near, far, fov, up, lookAt, position } =
                customCoords.getCameraParams();

            // 2D 地图下使用的正交相机
            // var { near, far, top, bottom, left, right, position, rotation } = customCoords.getCameraParams();

            // 这里的顺序不能颠倒，否则可能会出现绘制卡顿的效果。
            camera.near = near;
            camera.far = far;
            camera.fov = fov;
            camera.position.set(...position);
            camera.up.set(...up);
            camera.lookAt(...lookAt);
            camera.updateProjectionMatrix();

            // 2D 地图使用的正交相机参数赋值
            // camera.top = top;
            // camera.bottom = bottom;
            // camera.left = left;
            // camera.right = right;
            // camera.position.set(...position);
            // camera.updateProjectionMatrix();

            renderer.render(scene, camera);

            // 这里必须执行！！重新设置 three 的 gl 上下文状态。
            renderer.resetState();
        },
    });
    //endregion 创建 GL 图层

    // 在地图上添加图层
    if(globalThis.buildingLayer != null){
        globalThis.map.remove(globalThis.buildingLayer);//删除旧图层
    }
    globalThis.buildingLayer = gllayer
    globalThis.map.add(gllayer);//添加新图层

    function onWindowResize() { 
        camera.aspect = window.innerWidth / window.innerHeight; 
        camera.updateProjectionMatrix(); 
        renderer.setSize(window.innerWidth, window.innerHeight); 
    } 
    window.addEventListener('resize', onWindowResize);
}
function showBuildings(){
    if(globalThis.buildingLayer!=null){
        globalThis.buildingLayer.show();
    }
}
function hideBuildings(){
    if(globalThis.buildingLayer!=null){
        globalThis.buildingLayer.hide();
    }
}
// endregion显示建筑模型
// region选择起终点
var startIcon = new AMap.Icon({
    size: new AMap.Size(25, 34),
    image: '//a.amap.com/jsapi_demos/static/demo-center/icons/dir-marker.png',
    imageSize: new AMap.Size(135, 40),
    imageOffset: new AMap.Pixel(-9, -3)
});
var endIcon = new AMap.Icon({
    size: new AMap.Size(25, 34),
    image: '//a.amap.com/jsapi_demos/static/demo-center/icons/dir-marker.png',
    imageSize: new AMap.Size(135, 40),
    imageOffset: new AMap.Pixel(-95, -3)
});
function chooseStartEnd(){
    // 去除旧起点和终点
    if(globalThis.startMarker != null){
        globalThis.startMarker.setMap(null);
        globalThis.endMarker.setMap(null);
        globalThis.startMarker = null;
        globalThis.endMarker = null;
    }
    // 绘制起终点
    var mouseTool = new AMap.MouseTool(map)
    mouseTool.on('draw',function(event){
        if(globalThis.startMarker == null){
            event.obj.setIcon(startIcon);
            globalThis.startMarker = event.obj;
            log.info('起点选择完成');
        }
        else{
            event.obj.setIcon(endIcon);
            globalThis.endMarker = event.obj;
            log.info('终点选择完成');
            mouseTool.close();
        }
    })
    mouseTool.marker();
}
// endregion选择起终点
// region计算航摄路径
function calculateObstacleRoute(){
    log.info("obstacle");
    if(globalThis.endMarker == null){
        log.info('请先确定起终点');
    }
    else{
        route = getRoute("obstacle");
        drawRoute(route,"obstacle");
    }
}
function calculateAreaRoute(){
    log.info("area");
    route = getRoute("area");
    drawRoute(route,"area");
}
function getRoute(rType){
    log.info(rType)
    if(rType == "obstacle"){
        var start = globalThis.startMarker.getPosition();
        var end = globalThis.startMarker.getPosition();
        var start_wgs84 = coordtransform.gcj02towgs84(start.getLng(),start.getLat())
        var end_wgs84 = coordtransform.gcj02towgs84(end.getLng(),end.getLat())
        var upload_data = {
            "route_type":"obstacle",
            "start" : [start_wgs84[0],start_wgs84[1]],
            "end" : [end_wgs84[0],end_wgs84[1]],
        }
    }
    else if(rType == "area"){
        var upload_data = {
            "route_type":"area",
        }
    }
    var route_wgs84;
    var getRoute_url = "/routeplan3d/get-route";
        $.ajax({
            async:false,
            url: getRoute_url,
            type: "POST",
            dateType:'json',
            data: upload_data,
            headers:{
                "X-CSRFtoken":$.cookie("csrftoken"),
            },
            success:function (data) {
                log.info("计算航摄路径结束")
                route_wgs84 = data["route"]
            }
        })
    var route_gcj02 = []
    for(var i = 0; i < route_wgs84.length; ++i){
        var point_wgs84 = route_wgs84[i];
        var lnglat_wgs84 = point_wgs84["lnglat"];
        var lnglat_gcj02 = coordtransform.wgs84togcj02(lnglat_wgs84[0], lnglat_wgs84[1])
        route_gcj02.push({
            "lnglat": lnglat_gcj02,
            "height": point_wgs84["height"],
        })
    }
    return route_gcj02
}
function drawRoute(route_gcj02,rType){
    var camera;
    var renderer;
    var scene;
    var meshes = [];
    //region 数据转换:gcj02-map
    // 数据转换工具
    var customCoords = globalThis.map.customCoords;
    var routeLngLatList_gcj02 = []
    for(var i = 0; i < route_gcj02.length; ++i){
        routeLngLatList_gcj02.push(route_gcj02[i]["lnglat"])
    }
    window.alert(routeLngLatList_gcj02)
    var routeLngLatList_map = customCoords.lngLatsToCoords(routeLngLatList_gcj02);
    var route_map = []
    for(var i = 0; i < route_gcj02.length; ++i){
        route_map.push({
            "lnglat":routeLngLatList_map[i],
            "height":route_gcj02[i]["height"],
        })
    }
    //endregion

    // region 创建 GL 图层
    var gllayer = new AMap.GLCustomLayer({
        // 图层的层级
        zIndex: 10,
        // 初始化的操作，创建图层过程中执行一次。
        init: (gl) => {
            //region 相机和场景设置
            // 这里我们的地图模式是 3D，所以创建一个透视相机，相机的参数初始化可以随意设置，因为在 render 函数中，每一帧都需要同步相机参数，因此这里变得不那么重要。
            // 如果你需要 2D 地图（viewMode: '2D'），那么你需要创建一个正交相机
            camera = new THREE.PerspectiveCamera(
                60,
                window.innerWidth / window.innerHeight,
                100,
                1 << 30
            );

            renderer = new THREE.WebGLRenderer({
                context: gl, // 地图的 gl 上下文
                // alpha: true,
                // antialias: true,
                // canvas: gl.canvas,
            });

            // 自动清空画布这里必须设置为 false，否则地图底图将无法显示
            renderer.autoClear = false;
            scene = new THREE.Scene();

            // 环境光照和平行光
            var aLight = new THREE.AmbientLight(0xffffff, 0.3);
            var dLight = new THREE.DirectionalLight(0xffffff, 1);
            dLight.position.set(1000, -100, 900);
            scene.add(dLight);
            scene.add(aLight);
            //endregion 相机和场景设置

            //region 绘制
            // 材质设定
            var routeMaterial = new THREE.LineBasicMaterial({
                color: 'blue' //线条颜色
            }); 
            // 路径生成
            var routeGeometry = new THREE.BufferGeometry() //几何体初始化
            var route3D = []
            for(var i = 0; i < route_map.length; ++i){
                var lnglat = route_map[i]["lnglat"]
                var h = route_map[i]["height"]
                route3D.push(lnglat[0],lnglat[1],h)
            }
            var routeVertices = new Float32Array(route3D)
            routeGeometry.attributes.position = new THREE.BufferAttribute(routeVertices, 3)
            var routeLine = new THREE.Line(routeGeometry, routeMaterial);
            scene.add(routeLine);
            //endregion
        },
        render: () => {
            // 这里必须执行！！重新设置 three 的 gl 上下文状态。
            renderer.resetState();
            // 重新设置图层的渲染中心点，将模型等物体的渲染中心点重置
            // 否则和 LOCA 可视化等多个图层能力使用的时候会出现物体位置偏移的问题
            //customCoords.setCenter([116.29932,39.98456]);
            var { near, far, fov, up, lookAt, position } =
                customCoords.getCameraParams();

            // 2D 地图下使用的正交相机
            // var { near, far, top, bottom, left, right, position, rotation } = customCoords.getCameraParams();

            // 这里的顺序不能颠倒，否则可能会出现绘制卡顿的效果。
            camera.near = near;
            camera.far = far;
            camera.fov = fov;
            camera.position.set(...position);
            camera.up.set(...up);
            camera.lookAt(...lookAt);
            camera.updateProjectionMatrix();

            // 2D 地图使用的正交相机参数赋值
            // camera.top = top;
            // camera.bottom = bottom;
            // camera.left = left;
            // camera.right = right;
            // camera.position.set(...position);
            // camera.updateProjectionMatrix();

            renderer.render(scene, camera);

            // 这里必须执行！！重新设置 three 的 gl 上下文状态。
            renderer.resetState();
        },
    });
    //endregion 创建 GL 图层

    // 在地图上添加图层
    if(rType == "obstacle"){
        if(globalThis.obstacleRouteLayer != null){
            globalThis.map.remove(globalThis.obstacleRouteLayer);//删除旧图层
        }
        globalThis.obstacleRouteLayer = gllayer
        globalThis.map.add(gllayer);//添加新图层
    }
    else if(rType == "area"){
        if(globalThis.areaRouteLayer != null){
            globalThis.map.remove(globalThis.areaRouteLayer);//删除旧图层
        }
        globalThis.areaRouteLayer = gllayer
        globalThis.map.add(gllayer);//添加新图层
    }

    function onWindowResize() { 
        camera.aspect = window.innerWidth / window.innerHeight; 
        camera.updateProjectionMatrix(); 
        renderer.setSize(window.innerWidth, window.innerHeight); 
    } 
    window.addEventListener('resize', onWindowResize);
}
function showObstacleRoute(){
    if(globalThis.endMarker!=null){
        globalThis.startMarker.show();
        globalThis.endMarker.show();
    }
    if(globalThis.obstacleRouteLayer!=null){
        globalThis.obstacleRouteLayer.show();
    }
}
function hideObstacleRoute(){
    if(globalThis.endMarker!=null){
        globalThis.startMarker.hide();
        globalThis.endMarker.hide();
    }
    if(globalThis.obstacleRouteLayer!=null){
        globalThis.obstacleRouteLayer.hide();
    }
}
function showAreaRoute(){
    if(globalThis.areaRouteLayer != null){
        globalThis.obstacleRouteLayer.show();
    }
}
function hideAreaRoute(){
    if(globalThis.areaRouteLayer != null){
        globalThis.obstacleRouteLayer.hide();
    }
}
// endregion计算航摄路径