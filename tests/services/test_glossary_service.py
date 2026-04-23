import random
from uuid import uuid4

import pandas as pd
from faker import Faker

from app.api.v1.dto.requests.glossary import GlossaryElementsGetRequest, GlossaryElementsListRequest
from app.api.v1.dto.responses.glossary import (
    GlossaryElementsGetResponse,
    GlossaryElementsListResponse,
)
from app.domain.schemas.glossary_element import GlossaryElementSchema, GlossaryElementsUpToDateData
from app.infrastructure.adapters.excel import ExcelAdapter
from app.infrastructure.models import GlossaryElement
from app.services.interfaces import IGlossaryService
from app.settings.config import settings


class TestGlossaryService:
    """Тесты для сервиса глоссария"""

    async def test_clean_up_df_and_identify_errors(
        self, glossary_service: IGlossaryService
    ) -> None:
        """Получение очищенного от ошибок DataFrame и возврат ошибок"""
        df_dirty: pd.DataFrame = pd.DataFrame(
            {
                "abbreviation": [
                    "КИС ЕМИАС",
                    "КИС ЕМИАС",
                    "",
                    "только-аббревиатура",
                    "",
                    "",
                    "Lorem ipsum dolor sit amet. Qui galisum optio est accusantium magnam rem "
                    "pariatur dolor eos suscipit voluptatum et exercitationem quia. "
                    "Qui natus maiores sit earum voluptate et eius officiis 33 placeat officia ea "
                    "galisum repudiandae id quidem doloribus in placeat aliquid. "
                    "Est repellat officia est dolorem reiciendis sit corrupti saepe id blanditiis "
                    "optio sed eius saepe est praesentium dolorem sed corrupti velit. "
                    "Non molestiae voluptatem ut dolor dolores et eligendi fugiat ut quisquam "
                    "eaque nam reprehenderit deserunt.",
                ],
                "term": [
                    "Клиническая информационная система ЕМИАС",
                    "Клиническая информационная система ЕМИАС",
                    "",
                    "",
                    "только-термин",
                    "",
                    "текст...",
                ],
                "definition": [
                    "ЕМИАС в стационарах",
                    "ЕМИАС в стационарах",
                    "",
                    "",
                    "",
                    "только-определение",
                    "текст...",
                ],
            }
        )
        df_cleaned: pd.DataFrame
        df_errors: pd.DataFrame
        df_cleaned, df_errors = ExcelAdapter.clean_up_df_and_identify_errors(df=df_dirty)

        assert df_cleaned.to_dict() == {
            "abbreviation": {0: "КИС ЕМИАС"},
            "term": {0: "Клиническая информационная система ЕМИАС"},
            "definition": {0: "ЕМИАС в стационарах"},
        }
        assert df_errors.to_dict() == {
            "№ строки": {0: 3, 1: 4, 2: 5, 3: 6, 4: 7, 5: 8},
            "Тип ошибки": {
                0: "Дубликат",
                1: "Пустая строка",
                2: "Строка не заполнена полностью",
                3: "Строка не заполнена полностью",
                4: "Строка не заполнена полностью",
                5: "Аббревиатура длиннее 500 символов",
            },
            "Аббревиатура": {
                0: "КИС ЕМИАС",
                1: "",
                2: "только-аббревиатура",
                3: "",
                4: "",
                5: "Lorem ipsum dolor sit amet. Qui galisum optio est accusantium "
                "magnam rem pariatur dolor eos suscipit voluptatum et exercitationem quia. "
                "Qui natus maiores sit earum voluptate et eius officiis 33 placeat officia "
                "ea galisum repudiandae id quidem doloribus in placeat aliquid. Est repellat "
                "officia est dolorem reiciendis sit corrupti saepe id blanditiis optio sed "
                "eius saepe est praesentium dolorem sed corrupti velit. Non molestiae "
                "voluptatem ut dolor dolores et eligendi fugiat ut quisquam eaque nam reprehenderit deserunt.",
            },
            "Термин": {
                0: "Клиническая информационная система ЕМИАС",
                1: "",
                2: "",
                3: "только-термин",
                4: "",
                5: "текст...",
            },
            "Определение": {
                0: "ЕМИАС в стационарах",
                1: "",
                2: "",
                3: "",
                4: "только-определение",
                5: "текст...",
            },
        }

    async def test_prepare_glossary_data_to_update(
        self, glossary_service: IGlossaryService, faker: Faker
    ) -> None:
        """Подготовка данных к обновлению глоссария"""
        amount_of_existing = faker.pyint(min_value=1, max_value=50)
        elements_from_db: list[GlossaryElementSchema] = [
            GlossaryElementSchema(
                id=uuid4(),
                abbreviation=faker.pystr(min_chars=1, max_chars=500),
                term=faker.pystr(min_chars=1),
                definition=faker.pystr(min_chars=1),
            )
            for _ in range(amount_of_existing)
        ]

        amount_of_leftovers = faker.pyint(min_value=1, max_value=amount_of_existing)
        leftovers_schemas: list[GlossaryElementSchema] = random.sample(
            elements_from_db, k=amount_of_leftovers
        )
        leftovers_dicts: list[dict] = [reupdate.model_dump() for reupdate in leftovers_schemas]
        leftovers_dict = {
            "abbreviation": [],
            "term": [],
            "definition": [],
        }
        for item in leftovers_dicts:
            leftovers_dict["abbreviation"].append(item["abbreviation"])
            leftovers_dict["term"].append(item["term"])
            leftovers_dict["definition"].append(item["definition"])

        amount_of_new = faker.pyint(
            min_value=amount_of_leftovers, max_value=amount_of_leftovers + 20
        )
        df_cleaned = pd.DataFrame.from_dict(
            {
                "abbreviation": [
                    faker.pystr(min_chars=1, max_chars=500) for _ in range(amount_of_new)
                ]
                + leftovers_dict["abbreviation"],
                "term": [faker.pystr(min_chars=1) for _ in range(amount_of_new)]
                + leftovers_dict["term"],
                "definition": [faker.pystr(min_chars=1) for _ in range(amount_of_new)]
                + leftovers_dict["definition"],
            }
        )

        result: GlossaryElementsUpToDateData = glossary_service._prepare_glossary_data_to_update(
            elements_from_db, df_cleaned
        )

        assert amount_of_new == len(result.elements_to_create)
        assert amount_of_existing - len(result.raw_elements_to_delete) == amount_of_leftovers

    async def test_get_glossary_elements(
        self,
        real_glossary_elements: list[GlossaryElement],
        faker: Faker,
        glossary_service: IGlossaryService,
    ) -> None:
        """Получение элементов глоссария"""
        result: GlossaryElementsGetResponse = await glossary_service.get_glossary_elements(
            request=GlossaryElementsGetRequest(query="Отделение")
        )
        result_raw_no_definition = [
            {"abbreviation": el.abbreviation, "term": el.term} for el in result.data
        ]
        assert result_raw_no_definition == [
            {"abbreviation": "КДО", "term": "Консультативно-диагностическое отделение"},
            {
                "abbreviation": "КДО ЦПСиР",
                "term": "Консультативно-диагностическое отделение Центра планирования семьи и репродукции",
            },
            {"abbreviation": "ОАОП", "term": "Отделение антенатальной охраны плода"},
            {"abbreviation": "ОМП", "term": "Отделение медицинской профилактики"},
            {"abbreviation": "ОНМП", "term": "Отделение неотложной медицинской помощи"},
            {"abbreviation": "ОП", "term": "Отделение профилактики"},
            {"abbreviation": "ОРИТ", "term": "Отделение реанимации и интенсивной терапии"},
            {"abbreviation": "ПАО", "term": "Патологоанатомическое отделение (бюро)"},
            {"abbreviation": "ПОГБ", "term": "Поликлиническое отделение городской больницы"},
            {"abbreviation": "", "term": "Танатологическое отделение"},
        ]

        result: GlossaryElementsGetResponse = await glossary_service.get_glossary_elements(
            request=GlossaryElementsGetRequest(query="РМ", limit=250)
        )
        result_raw_no_definition = [
            {"abbreviation": el.abbreviation, "term": el.term} for el in result.data
        ]
        assert result_raw_no_definition == [
            {"abbreviation": "РМ", "term": "Расходный материал РМ"},
            {"abbreviation": "РМИС", "term": "Региональная медицинская информационная система"},
            {
                "abbreviation": "РМНН",
                "term": "Расширенное международное непатентованное наименование лекарственного препарата",
            },
            {"abbreviation": "РМО", "term": "Регистр медицинских организаций ЕМИАС"},
            {"abbreviation": "РМОГ", "term": "Реестр медицинских освидетельствований граждан"},
            {
                "abbreviation": "РМОМР",
                "term": "Реестр медицинских организаций и медицинских работников",
            },
            {"abbreviation": "РМР", "term": "Реестр медицинских работников"},
            {"abbreviation": "РМУ", "term": "Реестр медицинских учреждений"},
            {"abbreviation": "АРМ", "term": "Автоматизированное рабочее место"},
            {
                "abbreviation": "АРМ ЕМИАС",
                "term": "Автоматизированное рабочее место для пользователей ЕМИАС",
            },
            {
                "abbreviation": 'ГМТ, ГАУ "Гормедтехника"',
                "term": "Государственное автономное учреждение г. "
                'Москвы "Гормедтехника Департамента здравоохранения г. Москвы"',
            },
            {"abbreviation": "МобАРМ", "term": "Мобильное автоматизированное рабочее место"},
            {"abbreviation": "ФРМО", "term": "Федеральный реестр медицинских организаций ЕГИСЗ"},
            {"abbreviation": "ФРМР", "term": "Федеральный реестр медицинских работников ЕГИСЗ"},
            {"abbreviation": "ШРМ", "term": "Шкала реабилитационной маршрутизации"},
            {
                "abbreviation": "АИС МГФОМС",
                "term": "Автоматизированная информационная система обязательного медицинского "
                "страхования Московского городского фонда обязательного медицинского страхования",
            },
            {"abbreviation": "АФЗ", "term": "Автоматическое формирование заболеваний"},
            {"abbreviation": "АМГ", "term": "Антимюллеров гормон"},
            {"abbreviation": "ГТ", "term": "Гормоноиммунотерапевтическое лечение"},
            {"abbreviation": "ДИТ", "term": "Департамент информационных технологий г. Москвы"},
            {
                "abbreviation": "ДИТиС МЗ",
                "term": "Департамент информационных технологий и связи Министерства "
                "здравоохранения Российской Федерации",
            },
            {"abbreviation": "", "term": "Диапазон нормы параметра пациента"},
            {
                "abbreviation": "ЕАИСТ",
                "term": "Единая автоматизированная информационная система торгов г. Москвы",
            },
            {
                "abbreviation": "ЕГИСЗ",
                "term": "Единая государственная информационная система в сфере здравоохранения",
            },
            {"abbreviation": "ЕИС", "term": "Единая информационная система в сфере закупок"},
            {
                "abbreviation": "ЕМИАС",
                "term": "Единая медицинская информационно-аналитическая система г. Москвы",
            },
            {"abbreviation": "ЕРИС", "term": "Единая радиологическая информационная система"},
            {
                "abbreviation": "ЕИТП ЗАГС",
                "term": "Единое информационно-телекомуникационное пространство "
                "Управления записи актов гражданского состояния г. Москвы",
            },
            {"abbreviation": "ЕИРЦ", "term": "Единый информационный расчетный центр"},
            {"abbreviation": "ИФА", "term": "Иммуноферментный анализ"},
            {
                "abbreviation": "ИШ ЕРЗ",
                "term": "Интеграционный шлюз Единой медицинской информационно-аналитической системы г. Москвы",
            },
            {"abbreviation": "ИС", "term": "Информационная система"},
            {
                "abbreviation": "ИС ПП",
                "term": 'Информационная система "Проход и питание" в образовательных учреждениях г. Москвы',
            },
            {"abbreviation": "ИКТ", "term": "Информационно-коммуникационные технологии"},
            {"abbreviation": "ИР", "term": "Информационные ресурсы"},
            {
                "abbreviation": "ИСиР ОИВ",
                "term": "Информационные системы и ресурсы органов исполнительной власти г. Москвы",
            },
            {"abbreviation": "ИТ", "term": "Информационные технологии"},
            {"abbreviation": "ИАЦ", "term": "Информационный аналитический центр"},
            {"abbreviation": "ИК", "term": "Информационный киоск; инфомат"},
            {"abbreviation": "", "term": "Информер"},
            {
                "abbreviation": "ИДС",
                "term": "Информированное добровольное согласие на медицинское вмешательство",
            },
            {"abbreviation": "КИС ЕМИАС", "term": "Клиническая информационная система ЕМИАС"},
            {
                "abbreviation": "КИС ГУСОЭВ",
                "term": 'Комплексная информационная система "Государственные '
                'услуги в сфере образования в электронном виде"',
            },
            {"abbreviation": "КСИБ", "term": "Комплексная система информационной безопасности"},
            {"abbreviation": "ЛИС", "term": "Лабораторная информационная система"},
            {"abbreviation": "МИС", "term": "Медицинская информационная система"},
            {
                "abbreviation": "МИС МО",
                "term": "Медицинская информационная система медицинской организации",
            },
            {
                "abbreviation": "МСПС",
                "term": "Медицинское свидетельство о перинатальной смерти, форма 106-2-2/у-08",
            },
            {"abbreviation": "МСС", "term": "Медицинское свидетельство о смерти, форма 106/у-08"},
            {"abbreviation": "НСИ", "term": "Нормативно-справочная информация"},
            {"abbreviation": "НПА", "term": "Нормативный правовой акт"},
            {
                "abbreviation": "НСЗ ТФОМС",
                "term": "Нормированный страховой запас территориального фонда обязательного медицинского страхования",
            },
            {
                "abbreviation": "ОКОПФ",
                "term": "Общероссийский классификатор организационно-правовых форм",
            },
            {"abbreviation": "ОКФС", "term": "Общероссийский классификатор форм собственности"},
            {
                "abbreviation": "ГМКЦРИТ",
                "term": 'ООО "Городской медицинский компьютерный центр распределительных информационных технологий"',
            },
            {"abbreviation": "ПФ", "term": "Печатная форма"},
            {
                "abbreviation": "ПФПИ",
                "term": "Подсистема формирования пользовательского интерфейса ЕМИАС",
            },
            {"abbreviation": "ПКДФ", "term": "Призывная комиссия добровольческих формирований"},
            {"abbreviation": "РТСД", "term": "Радио-терминал сбора данных"},
            {"abbreviation": "РИС", "term": "Радиологическая информационная система"},
            {"abbreviation": "РЕИС", "term": "Региональная единая информационная система"},
            {"abbreviation": "СИМИ", "term": "Система интегрированной медицинской информации"},
            {
                "abbreviation": "СУДИР",
                "term": "Система управления доступом к информационным ресурсам",
            },
            {
                "abbreviation": "СУ НСИ",
                "term": "Система управления нормативно-справочной информацией",
            },
            {"abbreviation": "СКЗИ", "term": "Средство криптографической защиты информации"},
            {"abbreviation": "УФ ДЗМ", "term": "Управление фармации ДЗМ"},
            {"abbreviation": "УФ", "term": "Учетная форма"},
            {"abbreviation": "", "term": "Учетные формы"},
            {"abbreviation": "ФК", "term": "Фармацевтическая компания"},
            {
                "abbreviation": "ФГИС МДЛП, МДЛП",
                "term": "Федеральная государственная информационная система мониторинга "
                "движения лекарственных препаратов от производителя до "
                "конечного потребителя с использованием маркировки",
            },
            {"abbreviation": "ФИАС", "term": "Федеральная информационная адресная система"},
            {
                "abbreviation": "030-6/ГРР",
                "term": "Форма № 030-6/ГРР Регистрационная карта больного злокачественным заболеванием",
            },
            {"abbreviation": "", "term": "Форма №12"},
            {"abbreviation": "", "term": "Форма №16-ВН"},
            {"abbreviation": "", "term": "Форма №32"},
            {"abbreviation": "", "term": "Форма №57"},
            {"abbreviation": "", "term": "Формализованные поля"},
            {"abbreviation": "ФЛК", "term": "Форматно-логический контроль"},
            {
                "abbreviation": "ЦМиСРИТФ ДЦП",
                "term": "Центр медицинской и социальной реабилитации инвалидов с тяжелыми формами ДЦП",
            },
            {"abbreviation": "ЦИС", "term": "Централизованные информационные системы"},
            {"abbreviation": "ЭФ", "term": "Экранная Форма"},
        ]

        result: GlossaryElementsGetResponse = await glossary_service.get_glossary_elements(
            request=GlossaryElementsGetRequest(query="ОМС")
        )
        result_raw_no_definition = [
            {"abbreviation": el.abbreviation, "term": el.term} for el in result.data
        ]
        assert result_raw_no_definition == [
            {"abbreviation": "ОМС", "term": "Обязательное медицинское страхование"},
            {
                "abbreviation": "МГП ОМС",
                "term": "Московская городская программа обязательного медицинского страхования",
            },
            {"abbreviation": "Полис ОМС", "term": "Полис обязательного медицинского страхования"},
            {
                "abbreviation": "АИС МГФОМС",
                "term": "Автоматизированная информационная система обязательного медицинского "
                "страхования Московского городского фонда обязательного медицинского страхования",
            },
            {
                "abbreviation": "МГФОМС",
                "term": "Московский городской фонд обязательного медицинского страхования",
            },
            {
                "abbreviation": "НСЗ ТФОМС",
                "term": "Нормированный страховой запас территориального фонда обязательного медицинского страхования",
            },
            {"abbreviation": "ФОМС", "term": "Фонд обязательного медицинского страхования"},
            {"abbreviation": "БМИ", "term": "Базовая межведомственная инфраструктура"},
            {"abbreviation": "МРГ", "term": "Межведомственная рабочая группа"},
            {
                "abbreviation": "ПУУЗ БМИ",
                "term": "Подсистема управления учетными записями базовой межведомственной инфраструктуры",
            },
            {
                "abbreviation": "РСМЭВ",
                "term": "Региональная система межведомственного электронного взаимодействия",
            },
            {
                "abbreviation": "СМЭВ",
                "term": "Система межведомственного электроного взаимодействия",
            },
            {"abbreviation": "УПВС ДЗМ", "term": "Учреждения подведомственной сети ДЗМ"},
        ]

        result: GlossaryElementsGetResponse = await glossary_service.get_glossary_elements(
            request=GlossaryElementsGetRequest(query="Центр", limit=50)
        )
        result_raw_no_definition = [
            {"abbreviation": el.abbreviation, "term": el.term} for el in result.data
        ]
        assert result_raw_no_definition == [
            {
                "abbreviation": "ЦС, Центр Сухаревой",
                "term": "Научно-практический центр психического здоровья детей и подростков им. Г.Е. Сухаревой ДЗМ",
            },
            {"abbreviation": "АПЦ", "term": "Амбулаторно поликлинический центр"},
            {"abbreviation": "АЦ", "term": "Амбулаторный центр"},
            {"abbreviation": "АЦГП", "term": "Амбулаторный центр городской поликлиники"},
            {
                "abbreviation": "ГКДЦСИМ",
                "term": "Городской консультативно-диагностический центр по специфической иммунопрофилактике",
            },
            {
                "abbreviation": "ГАУЗ МНПЦ МРВСМ ДЗМ",
                "term": "Государственное автономное учреждение здравоохранения "
                '"Московский научно-практический центр медицинской реабилитации восстановительной '
                'и спортивной медицины Департамента здравоохранения Москвы"',
            },
            {
                "abbreviation": "ГППЦ",
                "term": "Государственное бюджетное учреждение г. Москвы "
                '"Городской психолого-педагогический центр Департамента образования и науки г. Москвы"',
            },
            {"abbreviation": "ЕИРЦ", "term": "Единый информационный расчетный центр"},
            {"abbreviation": "ЕЦП", "term": "Единый центр помощи участников СВО"},
            {"abbreviation": "ИАЦ", "term": "Информационный аналитический центр"},
            {"abbreviation": "КДЦ", "term": "Консультативно-диагностический центр"},
            {"abbreviation": "КЦПЗ", "term": "Консультативный центр психического здоровья"},
            {
                "abbreviation": "КЦМР ДЗМ",
                "term": "Координационный центр медицинской реабилитации Департамента здравоохранения г. Москвы",
            },
            {"abbreviation": "МФЦ", "term": "Многофункциональный центр обслуживания населения"},
            {
                "abbreviation": "НПЦ ИК",
                "term": "Научно-практический центр интервенционной кардиоангиологии",
            },
            {"abbreviation": "НПЦ МР", "term": "Научно-практический центр медицинской радиологии"},
            {
                "abbreviation": "НПЦ ЭМП",
                "term": "Научно-практический центр экстренной медицинской помощи",
            },
            {
                "abbreviation": "ГМКЦРИТ",
                "term": 'ООО "Городской медицинский компьютерный центр распределительных информационных технологий"',
            },
            {"abbreviation": "СЦ", "term": "Специализированный центр"},
            {"abbreviation": "УЦ", "term": "Удостоверяющий центр"},
            {"abbreviation": "ЦАОП", "term": "Центр амбулаторной онкологической помощи"},
            {"abbreviation": "ЦВЛ", "term": "Центр восстановительного лечения"},
            {"abbreviation": "ЦВЛД", "term": "Центр восстановительного лечения для детей"},
            {"abbreviation": "ЦВМиР", "term": "Центр восстановительной медицины и реабилитации"},
            {
                "abbreviation": "ЦГСЭН",
                "term": "Центр государственного санитарно-эпидемиологического надзора",
            },
            {"abbreviation": "ЦК", "term": "Центр компетенции"},
            {"abbreviation": "ЦЛО", "term": "Центр лекарственного обеспечения ДЗМ"},
            {
                "abbreviation": "ЦЛОиКК",
                "term": "Центр лекарственного обеспечения и контроля качества",
            },
            {"abbreviation": "ЦМТ", "term": "Центр мануальной терапии"},
            {
                "abbreviation": "ЦМиСРИТФ ДЦП",
                "term": "Центр медицинской и социальной реабилитации инвалидов с тяжелыми формами ДЦП",
            },
            {"abbreviation": "ЦМЗ", "term": "Центр ментального здоровья"},
            {"abbreviation": "ЦМ", "term": "Центр мониторинга"},
            {"abbreviation": "ЦОД", "term": "Центр обработки данных"},
            {
                "abbreviation": "ЦОВЛ СПНП",
                "term": "Центр организации восстановительного лечения "
                "специализированной психоневрологической помощи детям",
            },
            {"abbreviation": "ЦПРиНР", "term": "Центр патологии речи и нейрореабилитации"},
            {"abbreviation": "ЦПСиР", "term": "Центр планирования семьи и репродукции"},
            {"abbreviation": "ЦТО", "term": "Центр телефонных обращений"},
            {
                "abbreviation": "ЦКДЛ",
                "term": "Централизованная клинико-диагностическая лаборатория",
            },
            {"abbreviation": "ЦИС", "term": "Централизованные информационные системы"},
            {"abbreviation": "ЦЛС", "term": "Централизованный лабораторный сервис"},
            {
                "abbreviation": "ЦПМПК",
                "term": "Центральная психолого-медико-педагогическая комиссия",
            },
            {
                "abbreviation": "АС ГУФ",
                "term": 'Автоматизированная система "Единая система автоматизации '
                'централизованного предоставления государственных услуг и контроля исполнения функций"',
            },
            {"abbreviation": "ID УЦ", "term": "Идентификатор проверки удостоверяющего центра"},
            {
                "abbreviation": "КДО ЦПСиР",
                "term": "Консультативно-диагностическое отделение Центра планирования семьи и репродукции",
            },
        ]

        result: GlossaryElementsGetResponse = await glossary_service.get_glossary_elements(
            request=GlossaryElementsGetRequest(query="протокол")
        )
        result_raw_no_definition = [
            {"abbreviation": el.abbreviation, "term": el.term} for el in result.data
        ]
        assert result_raw_no_definition == [
            {"abbreviation": "", "term": "Медицинский протокол; протокол"},
            {"abbreviation": "ПГОК", "term": "Протокол городского онкологического консилиума"},
            {"abbreviation": "ПОК", "term": "Протокол онкологического консилиума"},
            {"abbreviation": "ПОВО", "term": "Протокол осмотра врача онколога"},
            {"abbreviation": "ПСЦ", "term": "Протокол согласования цены"},
            {"abbreviation": "ЧЗП", "term": "Частично заполненный протокол"},
        ]

        result: GlossaryElementsGetResponse = await glossary_service.get_glossary_elements(
            request=GlossaryElementsGetRequest(query="АП", limit=70)
        )
        result_raw_no_definition = [
            {"abbreviation": el.abbreviation, "term": el.term} for el in result.data
        ]
        assert result_raw_no_definition == [
            {"abbreviation": "АП", "term": "Аналитическая подсистема"},
            {"abbreviation": "АПНЛ", "term": "Амбулаторное принудительное наблюдение и лечение"},
            {"abbreviation": "АПУ", "term": "Амбулаторно-поликлиническое учреждение"},
            {"abbreviation": "АПЦ", "term": "Амбулаторно поликлинический центр"},
            {
                "abbreviation": "Направление на ИИ",
                "term": "Направление на инструментальное исследование",
            },
            {
                "abbreviation": "Направление на МСЭ",
                "term": "Направление на медико-социальную экспертизу",
            },
            {"abbreviation": "ТАП", "term": "Талон амбулаторного пациента"},
            {"abbreviation": "ВКИ", "term": "Воздушно-капельная инфекция"},
            {"abbreviation": "", "term": "Горизонт записи"},
            {"abbreviation": "ГТ", "term": "Гормоноиммунотерапевтическое лечение"},
            {"abbreviation": "ГРЗ", "term": "Группа реестровых записей"},
            {"abbreviation": "", "term": "Диапазон нормы параметра пациента"},
            {
                "abbreviation": "ЕИТП ЗАГС",
                "term": "Единое информационно-телекомуникационное пространство "
                "Управления записи актов гражданского состояния г. Москвы",
            },
            {"abbreviation": "", "term": "Запись на прием к врачу"},
            {"abbreviation": "", "term": "Запись регистра"},
            {"abbreviation": "ЛТ", "term": "Лекарственная терапия"},
            {"abbreviation": "ЛТ", "term": "Лучевая терапия"},
            {"abbreviation": "", "term": "Медзапись"},
            {"abbreviation": "", "term": "Направление на прием"},
            {"abbreviation": "нМУ", "term": "Направляющее медицинское учреждение."},
            {
                "abbreviation": "НСЗ ТФОМС",
                "term": "Нормированный страховой запас территориального фонда "
                "обязательного медицинского страхования",
            },
            {"abbreviation": "ОДА", "term": "Опорно-двигательный аппарат"},
            {"abbreviation": "ОРИТ", "term": "Отделение реанимации и интенсивной терапии"},
            {
                "abbreviation": "ПУУЗ КМИ",
                "term": "Подсистема управления жизненным циклом учетных записей, "
                "сертификатов пользователей и ключевых носителей КМИ",
            },
            {
                "abbreviation": "ПУУЗ БМИ",
                "term": "Подсистема управления учетными записями базовой межведомственной инфраструктуры",
            },
            {"abbreviation": "ПАК", "term": "Программно-аппаратный комплекс"},
            {"abbreviation": "ППАК", "term": "Продуктивный программно-аппаратный контур"},
            {"abbreviation": "РЗ", "term": "Реестровая запись, реестр записей"},
            {"abbreviation": "", "term": "СУПП.Запись"},
            {"abbreviation": "ТПАК", "term": "Тестовый программно-аппаратный комплекс"},
            {"abbreviation": "ЗАГС", "term": "Управление записи актов гражданского состояния"},
            {"abbreviation": "ХТ", "term": "Химиотерапевтическое лечение; химиотерапия"},
            {"abbreviation": "ЦМТ", "term": "Центр мануальной терапии"},
            {"abbreviation": "ЧЗП", "term": "Частично заполненный протокол"},
            {"abbreviation": "ЧЗР", "term": "Частично заполненный раздел"},
        ]

        result_lowercase: GlossaryElementsGetResponse = (
            await glossary_service.get_glossary_elements(
                request=GlossaryElementsGetRequest(query="ЕМИАС", limit=250)
            )
        )
        result_uppercase: GlossaryElementsGetResponse = (
            await glossary_service.get_glossary_elements(
                request=GlossaryElementsGetRequest(query="емиас", limit=250)
            )
        )

        garbage_symbols = settings.app.glossary_request_garbage_symbols
        garbage_left = "".join(
            random.sample(garbage_symbols, k=faker.pyint(1, len(garbage_symbols)))
        )
        garbage_right = "".join(
            random.sample(garbage_symbols, k=faker.pyint(1, len(garbage_symbols)))
        )

        result_garbagesymbol: GlossaryElementsGetResponse = (
            await glossary_service.get_glossary_elements(
                request=GlossaryElementsGetRequest(
                    query=f"{garbage_left}ЕМИАС{garbage_right}", limit=250
                )
            )
        )
        assert result_lowercase == result_uppercase == result_garbagesymbol

    async def test_get_all_glossary_elements_with_pagination(
        self,
        glossary_element_factory,
        glossary_service: IGlossaryService,
    ) -> None:
        """Проверяет пагинацию, сортировку и корректный total."""
        await glossary_element_factory(
            abbreviation="CCC",
            term="term-3",
            definition="definition-3",
        )
        await glossary_element_factory(
            abbreviation="AAA",
            term="term-1",
            definition="definition-1",
        )
        await glossary_element_factory(
            abbreviation="BBB",
            term="term-2",
            definition="definition-2",
        )

        result: GlossaryElementsListResponse = await glossary_service.get_all_glossary_elements(
            request=GlossaryElementsListRequest(limit=2, offset=1)
        )

        assert [element.abbreviation for element in result.data] == ["BBB", "CCC"]
        assert result.count == 2
        assert result.total == 3

    async def test_get_all_glossary_elements_empty_page(
        self,
        glossary_element_factory,
        glossary_service: IGlossaryService,
    ) -> None:
        """Проверяет сценарий пустой страницы при offset за пределами выборки."""
        await glossary_element_factory(
            abbreviation="AAA",
            term="term-1",
            definition="definition-1",
        )
        await glossary_element_factory(
            abbreviation="BBB",
            term="term-2",
            definition="definition-2",
        )

        result: GlossaryElementsListResponse = await glossary_service.get_all_glossary_elements(
            request=GlossaryElementsListRequest(limit=10, offset=100)
        )

        assert result.data == []
        assert result.count == 0
        assert result.total == 2
