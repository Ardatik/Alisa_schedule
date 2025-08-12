def find_teacher(nlu):
    fio_data = {}
    entities = nlu.entities
    for entity in entities:
        entity_value = entity.value
        if entity.type == 'YANDEX.FIO':
            first_name = entity_value.get('first_name', '')
            last_name = entity_value.get('last_name', '')
            patronymic = entity_value.get('patronymic_name', '')
            if last_name:
                fio_data["last_name"] = last_name
            if first_name:
                fio_data["first_name"] = first_name
            if patronymic:
                fio_data["patronymic"] = patronymic
            full_name_parts = [i for i in [last_name, first_name, patronymic] if i]
            fio_data["full_name"] = " ".join(full_name_parts)
            break
    return fio_data