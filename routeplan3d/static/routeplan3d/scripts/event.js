var map;//地图
var mouseTool;//鼠标工具
var photoArea = null;//航摄区域
var buildingLayer = null;//3D建筑显示
var buildingList;//建筑数据

function bind_events(){
    // 绑定鼠标工具事件
    mouseTool.on('draw', mouseTool_draw);
    $("button#chooseArea").click(function(){chooseArea()});
    $("input#showArea").click(function(){showArea()});
    $("input#hideArea").click(function(){hideArea()});
    $("button#loadBuildings").click(function(){loadBuildings()});
    $("input#showBuildings").click(function(){showBuildings()});
    $("input#hideBuildings").click(function(){hideBuildings()});
}

$(document).ready(function(){
    /*加载地图*/
    load_map();
    bind_events()
})