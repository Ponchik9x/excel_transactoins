import datetime
import json
import logging

from utils import read_file_exel

logger = logging.getLogger("services")
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("logs/services.log", mode="w")
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


file = read_file_exel("data/operations.xlsx")


def get_increased_cashback(data: list[dict | dict], year: int, month: int) -> str:
    """
    :param data: Данные с транзакциями.
    :param year: Год, за который проводится анализ.
    :param month: Месяц, за который проводится анализ.
    :return:
    """
    logger.info(f"Получение списка транзакций и сортировка по году: {year} и по месяцу: {month}")

    result_dict_categories: dict = {}

    sorted_list = []
    for v in data:
        v["Дата операции"] = datetime.datetime.strptime(v["Дата операции"], "%d.%m.%Y %H:%M:%S")
        if v["Дата операции"].year == year and v["Дата операции"].month == month:
            sorted_list.append(v)

    logger.info("Получение списка с категориями и суммой кэшбека категории")
    for v in sorted_list:

        if v["Кэшбэк"] > 0:
            cashback = v["Кэшбэк"]

            if v["Категория"] in result_dict_categories:
                result_dict_categories[v["Категория"]] += cashback

            else:
                result_dict_categories[v["Категория"]] = cashback

    result = json.dumps(result_dict_categories)

    return result


if __name__ == "__main__":
    print(get_increased_cashback(file, 2021, 5))
