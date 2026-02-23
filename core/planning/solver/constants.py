from core.domain.enums.day_type import DayType

# Day types considérés comme indisponibilités dures
UNAVAILABLE_DAY_TYPES = {
    DayType.ABSENT.value,
    DayType.LEAVE.value,
}
