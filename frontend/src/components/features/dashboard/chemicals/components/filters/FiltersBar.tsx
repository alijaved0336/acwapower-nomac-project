"use client";
import React, { memo, useMemo } from "react";
import { useChemicalData } from "../../context/ChemicalDataContext";
import DateRangeFilter from "./DateRangeFilter";
import LocationFilters from "./LocationFilters";
import FilterCard from "../../../../racks-weighted/components/FilterCard";
import dayjs from "dayjs";

const FiltersBar: React.FC = memo(() => {
  const filterProps = useChemicalData();

  const defaultDateRange = useMemo(
    () => ({
      from_date: dayjs().subtract(7, "day").toISOString(),
      to_date: dayjs().toISOString(),
    }),
    []
  );

  const handleReset = () => {
    filterProps.resetAllFilters();
    filterProps.setDates(defaultDateRange);
  };

  return (
    <FilterCard inline onReset={handleReset}>
      <div className="flex items-center gap-8" style={{ width: "1300px" }}>
        <DateRangeFilter
          dates={filterProps.dates}
          setDates={(val) => {
            if (val && val.from_date && val.to_date) {
              filterProps.setDates({
                from_date: val.from_date,
                to_date: val.to_date,
              });
            }
          }}
        />

        <LocationFilters {...filterProps} />
      </div>
    </FilterCard>
  );
});

FiltersBar.displayName = "FiltersBar";

export default FiltersBar;
