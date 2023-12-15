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