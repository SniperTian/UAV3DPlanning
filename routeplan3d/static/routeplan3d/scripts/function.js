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
    // 获取选区范围
    var areaBounds = photoArea.getOptions().bounds
    var sw = areaBounds.getSouthWest()
    var ne = areaBounds.getNorthEast()
    // 坐标转换
    var sw_wgs84 = coordtransform.gcj02towgs84(sw.getLng(),sw.getLat())
    var ne_wgs84 = coordtransform.gcj02towgs84(ne.getLng(),ne.getLat())

    var upload_data = {
        "sw_wgs84": sw_wgs84,
        "ne_wgs84": ne_wgs84,
    }
    var showBuildings_url = "/routeplan3d/show-buildings"
    $.ajax({
        async:false,
        url: showBuildings_url,
        type: "POST",
        dateType:'json',
        data: upload_data,
        headers:{
            "X-CSRFtoken":$.cookie("csrftoken"),
        },
        success:function (data) {
            if(data["success"]==false)
            {
                window.alert("Wrong Answer!")
                qna_html.children('.question').children('button').text("答案错误")
            }
            else{
                window.alert("Correct!")
                qna_html.children('.question').children('button').text("答案正确")
                answer_now.children('textarea').attr('disabled',true)
                window.alert(data["text"])
                text_now.children('textarea').val(data["text"])
            }
        }
    })
}