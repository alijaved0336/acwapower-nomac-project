"use client";

import React from "react";
import { DatePicker, Flex, Grid } from "antd";
import { useRoRacksContext } from "../../context/RoRacksContext";
import dayjs, { Dayjs } from "dayjs";
import { DateFormat } from "@/constants/enums";
import { customLocale } from "@/utils/datePickerUtil";
import { useAppSelector } from "@/hooks";
import { getSiteDisplayName } from "@/utils/siteDisplayNames";

const { useBreakpoint } = Grid;

const Filters: React.FC = () => {
  const { selectedFilters, handleFilterChange, selectedSite } =
    useRoRacksContext();
  const selectedSiteGlobal = useAppSelector(
    (state) => state.siteSelection.selectedSite
  );

  // Use global site if available
  const siteToDisplay = selectedSite || selectedSiteGlobal;

  const size = useBreakpoint();
  const isMobile = !!size.xs;

  const handleDateChange = (date: Dayjs | null) => {
    handleFilterChange(
      "selectedDate",
      date ? dayjs(date).startOf("day") : null
    );
  };

  return (
    <Flex vertical gap={isMobile ? 0 : 12}>
      <Flex vertical gap={6}>
        <Flex
          align="center"
          justify="space-between"
          style={{ flexWrap: "wrap", gap: "12px" }}
        >
          <h2
            style={{
              padding: "12px",
              fontSize: "35px",
              fontWeight: 500,
              margin: 0,
              color: "#000",
            }}
          >
            RO Racks
          </h2>

          <Flex gap={8} align="center">
            {/* Site Indicator */}
            {siteToDisplay && (
              <div
                style={{
                  padding: "8px 12px",
                  background: "#e6f7ff",
                  borderRadius: "6px",
                  border: "1px solid #91d5ff",
                  fontSize: "13px",
                  color: "#666",
                }}
              >
                <strong>Site:</strong> {getSiteDisplayName(siteToDisplay)}
              </div>
            )}

            {/* 📅 Date Picker */}
            <div style={{ position: "relative" }}>
              <DatePicker
                showTime={{ format: "HH:mm:ss" }}
                value={selectedFilters.selectedDate}
                onChange={handleDateChange}
                locale={customLocale}
                placeholder="Select date & time"
                format={DateFormat.DATE_TIME_24H}
                size="middle"
                style={{
                  width: 220,
                  borderRadius: "8px",
                }}
              />
            </div>
          </Flex>
        </Flex>
      </Flex>
    </Flex>
  );
};

export default Filters;
