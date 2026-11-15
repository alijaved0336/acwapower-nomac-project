import { PickerLocale } from "antd/es/date-picker/generatePicker";

export const customLocale: PickerLocale = {
  lang: {
    locale: "en_US",
    placeholder: "Select date",
    rangePlaceholder: ["Start date", "End date"],
    today: "Today",
    now: "Now",
    week: "",
    backToToday: "Back to today",
    ok: "Apply", // Changed here
    clear: "Clear",
    month: "Month",
    year: "Year",
    timeSelect: "Select time",
    dateSelect: "Select date",
    monthSelect: "Choose a month",
    yearSelect: "Choose a year",
    decadeSelect: "Choose a decade",
    yearFormat: "YYYY",
    dateFormat: "DD/MM/YY",
    dayFormat: "D",
    dateTimeFormat: "DD/MM/YY HH:mm",
    monthFormat: "MMMM",
    monthBeforeYear: true,
    previousMonth: "Previous month",
    nextMonth: "Next month",
    previousYear: "Previous year",
    nextYear: "Next year",
    previousDecade: "Previous decade",
    nextDecade: "Next decade",
    previousCentury: "Previous century",
    nextCentury: "Next century",
  },
  timePickerLocale: {
    placeholder: "Select time",
  },
};
