from src.services import config_service
from src.utils.response import success_response, error_response

async def check_config():
    try:
        status = await config_service.get_config_status()
        return success_response(data=status)
    except Exception as e:
        return error_response(message=f"配置检查失败: {str(e)}", status_code=500)