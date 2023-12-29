var map;//地图
var mouseTool;//鼠标工具
var photoArea = null;//航摄区域
var buildingLayer = null;//3D建筑显示
var startMarker = null;//路径起点
var endMarker = null;//路径终点
var obstacleRouteLayer = null;//路径图层
var areaRouteLayer = null;

function bind_events(){
    // 绑定选择航摄区域相关功能
    $("button#chooseArea").click(function(){chooseArea()});
    $("input#showArea").click(function(){showArea()});
    $("input#hideArea").click(function(){hideArea()});
    // 绑定显示建筑模型相关功能
    $("button#loadBuildings").click(function(){loadBuildings()});
    $("input#showBuildings").click(function(){showBuildings()});
    $("input#hideBuildings").click(function(){hideBuildings()});
    // 绑定计算避障路径相关功能
    $("button#chooseStartEnd").click(function(){chooseStartEnd()});//选择起终点
    $("button#calculateObstacleRoute").click(function(){calculateObstacleRoute()});
    $("input#showObstacleRoute").click(function(){showObstacleRoute()});
    $("input#hideObstacleRoute").click(function(){hideObstacleRoute()});
    // 绑定计算区域路径相关功能
    $("button#calculateAreaRoute").click(function(){calculateAreaRoute()});
    $("input#showAreaRoute").click(function(){showAreaRoute()});
    $("input#hideAreaRoute").click(function(){hideAreaRoute()});

}

$(document).ready(function(){
    /*加载地图*/
    load_map();
    bind_events()
})