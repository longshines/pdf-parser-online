import gradio as gr
import opendataloader_pdf
import os
import shutil
import uuid
import threading

# 配置参数
MAX_FILE_SIZE_MB = 100  # 限制最大文件为 100MB
CLEANUP_DELAY_SECONDS = 300  # 5分钟后清理
BASE_TEMP_DIR = "./temp_sessions"

# 确保基础临时目录存在
os.makedirs(BASE_TEMP_DIR, exist_ok=True)

def cleanup_directory(dir_path):
    """后台清理任务：删除指定目录"""
    try:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            print(f"✅ 已清理过期会话目录: {dir_path}")
    except Exception as e:
        print(f"❌ 清理目录失败 {dir_path}: {e}")

def process_pdf(pdf_file, mode, formats):
    if not pdf_file:
        return None, "⚠️ 请先上传一个 PDF 文件。"
    
    # 1. 文件大小安全检查
    file_size_mb = os.path.getsize(pdf_file.name) / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        return None, f"⚠️ 文件过大 ({file_size_mb:.1f}MB)。为保证服务器稳定性，限制最大上传 {MAX_FILE_SIZE_MB}MB。"

    # 2. 并发隔离：为本次请求生成唯一的 UUID 会话目录
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(BASE_TEMP_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    format_str = ",".join(formats) if formats else "markdown,json"
    hybrid_val = mode if mode != "fast" else None

    try:
        # 3. 执行解析，输出到专属目录
        opendataloader_pdf.convert(
            input_path=[pdf_file.name],
            output_dir=session_dir,
            format=format_str,
            hybrid=hybrid_val
        )
        
        # 收集结果文件
        output_files = [os.path.join(session_dir, f) for f in os.listdir(session_dir)]
        
        if not output_files:
            return None, "⚠️ 解析完成，但没有生成任何文件。"
            
        return output_files, f"✅ 解析成功！文件将保留 {CLEANUP_DELAY_SECONDS//60} 分钟，请尽快下载。"
        
    except Exception as e:
        return None, f"❌ 解析失败: {str(e)}"
        
    finally:
        # 4. 无论成功还是失败，启动后台定时清理任务 (5分钟后执行)
        timer = threading.Timer(CLEANUP_DELAY_SECONDS, cleanup_directory, args=[session_dir])
        timer.daemon = True # 设置为守护线程，主程序退出时它也会退出
        timer.start()

# 构建 Gradio 网页界面
with gr.Blocks(title="PDF 智能解析器") as demo:
    gr.Markdown("## 📄 基于 OpenDataLoader 构建的 PDF 智能解析器")
    gr.Markdown("上传 PDF，选择解析模式和输出格式，即可提取 Markdown 或带坐标的 JSON。")
    
    with gr.Row():
        with gr.Column():
            file_input = gr.File(label=f"上传 PDF 文件 (最大 {MAX_FILE_SIZE_MB}MB)", file_types=[".pdf"])
            mode_input = gr.Dropdown(
                choices=["fast", "docling-fast"], 
                value="fast", 
                label="解析模式"
            )
            format_input = gr.CheckboxGroup(
                choices=["markdown", "json", "html"], 
                value=["markdown", "json"], 
                label="输出格式"
            )
            submit_btn = gr.Button("开始解析", variant="primary")
            
        with gr.Column():
            status_output = gr.Textbox(label="运行状态", interactive=False)
            file_output = gr.File(label="下载解析结果")

    submit_btn.click(
        fn=process_pdf,
        inputs=[file_input, mode_input, format_input],
        outputs=[file_output, status_output]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)