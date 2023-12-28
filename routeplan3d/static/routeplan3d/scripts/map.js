function load_map()
{
    // 加载地图
    map = new AMap.Map('map',{
        zoom : 15,
        viewMode: '3D', //3D模式
        pitch: 50,
        showBuildingBlock: false,
        showLabel: false,
    });
    // 引入控件和工具
    AMap.plugin([
        'AMap.ToolBar', //放大缩小工具条
        'AMap.Scale', //比例尺
        'AMap.MapType', //地图切换
        'AMap.Geolocation', //定位
        'AMap.MouseTool', //鼠标工具
    ], function() {
        geolocation = new AMap.Geolocation({
            position:'RT',    //定位按钮的停靠位置
            offset: [10, 20], //定位按钮与设置的停靠位置的偏移量，默认：[10, 20]
            zoomToAccuracy: true,   //定位成功后是否自动调整地图视野到定位点
            showMarker: false,
            showCircle: false,
        });
        toolbar = new AMap.ToolBar({
            position:'RT',
            offset: [10, 60],
        });
        maptype = new AMap.MapType({
            position:'RT',
            offset: [60, 20],
        })
        mouseTool = new AMap.MouseTool(map)
        map.addControl(new AMap.Scale());
    });
    map.addControl(geolocation);
    map.addControl(toolbar);
    map.addControl(maptype);
    // geolocation.getCurrentPosition(); //定位到当前位置
}
