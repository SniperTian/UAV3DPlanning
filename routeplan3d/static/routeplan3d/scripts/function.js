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
    buildingList = getBuildings(areaBounds)
    // 删除旧图层
    // 绘制建筑3D图层

}

function getBuildings(areaBounds){
    var sw = areaBounds.getSouthWest() //SouthWest
    var ne = areaBounds.getNorthEast() //NorthEast
    // 选区边界坐标转换 gcj02 -> wgs84
    var sw_wgs84 = coordtransform.gcj02towgs84(sw.getLng(),sw.getLat())
    var ne_wgs84 = coordtransform.gcj02towgs84(ne.getLng(),ne.getLat())
    var upload_data = {
        "area_bounds" : {
            "sw_lng" : sw_wgs84[0],
            "sw_lat" : sw_wgs84[1],
            "ne_lng" : ne_wgs84[0],
            "ne_lat" : ne_wgs84[1],
        },
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
            buildingList_wgs84 = data["buildingList_wgs84"]
        }
    })
    // 建筑坐标转换 wgs84 -> gcj02
    var buildingList_gcj02 = []
    for(var i = 0; i < buildingList_wgs84.length; ++i){
        var building_wgs84 = buildingList_wgs84[i];
        var polygonExterior_wgs84 = building_wgs84["polygonExterior_wgs84"];
        var mid = [];
        var polygonExterior_gcj02 = [];
        for(var j = 0; j<polygonExterior_wgs84.length; ++j){
            lnglat_wgs84 = polygonExterior_wgs84[j]
            mid[j] = new AMap.LngLat(lnglat_wgs84["lng"],lnglat_wgs84["lat"])
        };
        AMap.convertFrom(mid, 'gps', function (status, result) {
            if (result.info === 'ok') {
                polygonExterior_gcj02 = result.locations; // Array.<LngLat>
            }
        });
        buildingList_gcj02.append({
            "polygonExterior": polygonExterior_gcj02,
            "height": building_wgs84["height"],
        })
    }
    return buildingList_gcj02

}

function drawBuildings(){
    var camera;
    var renderer;
    var scene;
    var meshes = [];
    // 数据转换工具
    var customCoords = map.customCoords;

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

            var texture = new THREE.TextureLoader().load(
                'https://a.amap.com/jsapi_demos/static/demo-center-v2/three.jpeg'
            );
            texture.minFilter = THREE.LinearFilter;
            //  这里可以使用 three 的各种材质
            var mat = new THREE.MeshPhongMaterial({
                color: 0xfff0f0,
                depthTest: true,
                transparent: true,
                map: texture,
            });
            var geo = new THREE.BoxBufferGeometry(1000, 1000, 1000);
            for (let i = 0; i < data.length; i++) {
                const d = data[i];
                var mesh = new THREE.Mesh(geo, mat);
                mesh.position.set(d[0], d[1], 500);
                meshes.push({
                    mesh,
                    count: i,
                });
                scene.add(mesh);
            }
            //endregion
        },
        render: () => {
            // 这里必须执行！！重新设置 three 的 gl 上下文状态。
            renderer.resetState();
            // 重新设置图层的渲染中心点，将模型等物体的渲染中心点重置
            // 否则和 LOCA 可视化等多个图层能力使用的时候会出现物体位置偏移的问题
            customCoords.setCenter([116.52, 39.79]);
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
}