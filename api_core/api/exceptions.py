from api_basebone.core import exceptions


class NoSumitParameterLogic(exceptions.BusinessException):
    """
    客户端没有提交此参数
    """

    def __init__(self, param_name):
        super().__init__(
            error_code=exceptions.PARAMETER_FORMAT_ERROR,
            error_data=f'参数\'{param_name}\'为未定义参数',
        )
