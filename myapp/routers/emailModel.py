from fastapi import APIRouter
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

router = APIRouter();

@router.get('/email/send_email',tags=["邮件模块"], summary="测试发送邮件到指定邮箱")
async def sendEmail():
    """
    发送邮件。
    :param subject: 邮件主题
    :param body:邮件正文
    :param recipient:收件人邮箱地址
    """

    # 邮箱配置
    smtp_server = "smtp.163.com"
    smtp_port = 25
    username = "szrwlyp@163.com"
    # password = "szrwlyp0320..."
    password = "RNU4nbqkU3bTEW6J"  # 授权码
    # 接受者
    subject = "Hello from Python!"
    body = "测试测试"
    recipient = "1545763981@qq.com"

    # 创建MIME多部分消息
    message = MIMEText(body, "plain", "utf-8")
    message["From"] = username
    message["To"] = recipient
    message["Subject"] = subject

    try:
        # 创建SMTP对象
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)

        # 发送邮件
        server.sendmail(username, [recipient], message.as_string())
        print("邮件发送成功")
    except Exception as e:
        print(f"邮件发送失败：{e}")
    finally:
        server.quit()