// /src/components/features/racks/filters/DateFilter.tsx
import DateRangePicker from "@/components/common/widgets/DateRangePicker";
import dayjs, { Dayjs } from "dayjs";

interface DateFilterProps {
  dates: { from_date: string; to_date: string };
  onChange: (dates: { from_date: string; to_date: string }) => void;
}

export default function DateFilter({ dates, onChange }: DateFilterProps) {
  const handleChange = (newDates: [Dayjs | null, Dayjs | null] | null) => {
    if (newDates) {
      const [from, to] = newDates;
      onChange({
        from_date: from?.format("YYYY-MM-DD HH:mm:ss") || "",
        to_date: to?.format("YYYY-MM-DD HH:mm:ss") || "",
      });
    }
  };

  return (
    <div className="w-[420px]">
      <DateRangePicker
        onChange={handleChange}
        size="middle"
        value={[dayjs(dates.from_date), dayjs(dates.to_date)]}
        allowClear={true}
        disableFutureDates
        style={{
          width: "100%",
        }}
      />
    </div>
  );
}
