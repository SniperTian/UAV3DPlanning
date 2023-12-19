// 选择区域
function mouseTool_draw(event){
    // event.obj 为绘制出来的覆盖物对象
    photoArea = event.obj;
    //log.info(photoArea.getOptions().bounds)
    mouseTool.close()
    log.info('航摄区域选择完成')
    //log.info(photoArea.getOptions())
}
function chooseArea(){
    // 清除旧选区
    if(photoArea!=null){
        photoArea.destroy();
    }
    // 绘制新选区
    mouseTool.rectangle({
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

// 显示建筑模型
function showBuildings(){
    // region 获取建筑信息
    // 获取选区范围
    var areaBounds = photoArea.getOptions().bounds
    buildingList_gcj02 = getBuildings(areaBounds)
    // 删除旧图层
    // 绘制建筑3D图层
    drawBuildings(buildingList_gcj02)
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
    window.alert(buildingList_wgs84[0]["polygonExterior_wgs84"])
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
    // 数据转换工具
    var customCoords = map.customCoords;
    var buildingList_map = []
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
    //window.alert(buildingList_map[0]["polygonExterior"][0])


    // 创建3D图层
    // 创建 GL 图层
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
            var bulidingMaterial = new THREE.MeshBasicMaterial( { color: 0xff0000 } );

            for(var i = 1; i < buildingList_map.length; ++i){
                var building = buildingList_map[i]
                var polygonExterior = building["polygonExterior"]
                var pLength = polygonExterior.length
                var buildingHeight = 100*building["height"]
                //window.alert(polygonExterior);
                //window.alert(buildingHeight);
                var buildingGeometry = new THREE.BufferGeometry()
                //
                var buildingIndices = []
                for(var j = 0; j < pLength; ++j){
                    buildingIndices.push(j,j+1,pLength+j)
                    buildingIndices.push(j+1,pLength+j+1,pLength+j)
                }
                //window.alert(buildingIndices)

                buildingGeometry.setIndex(buildingIndices)
                //
                var polygonExterior3D = []
                for(var j = 0; j < pLength; ++j){
                    point = polygonExterior[j]
                    polygonExterior3D.push(point[0],point[1],0)
                }
                for(var j = 0; j < pLength; ++j){
                    point = polygonExterior[j]
                    polygonExterior3D.push(point[0],point[1],buildingHeight)
                }
                var buildingVertices = new Float32Array(polygonExterior3D)
                //window.alert(buildingVertices)
                buildingGeometry.setAttribute(
                    'position',
                    new THREE.BufferAttribute(buildingVertices, 3),
                )
                var buildingMesh = new THREE.Mesh(buildingGeometry,bulidingMaterial)
                meshes.push(buildingMesh)
                scene.add(buildingMesh)
            }
            //endregion
        },
        render: () => {
            // 这里必须执行！！重新设置 three 的 gl 上下文状态。
            renderer.resetState();
            // 重新设置图层的渲染中心点，将模型等物体的渲染中心点重置
            // 否则和 LOCA 可视化等多个图层能力使用的时候会出现物体位置偏移的问题
            customCoords.setCenter(map.getCenter());
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
    map.add(gllayer);

    function onWindowResize() { 
        camera.aspect = window.innerWidth / window.innerHeight; 
        camera.updateProjectionMatrix(); 
        renderer.setSize(window.innerWidth, window.innerHeight); 
    } 
    window.addEventListener('resize', onWindowResize);
}