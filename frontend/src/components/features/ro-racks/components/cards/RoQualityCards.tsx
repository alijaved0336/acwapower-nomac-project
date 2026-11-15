"use client";

import React, { FC } from "react";
import { useRoRacksContext } from "../../context/RoRacksContext";
import { formatRoKey } from "../../utils/roRacksUtils";

type CardItem = { value: number | string; unit?: string };

type Props = {
  pass: "firstPass" | "secondPass";
  cards: Record<string, CardItem>;
  loading?: boolean;
};

const RoQualityCards: FC<Props> = ({ pass, cards, loading }) => {
  const { isLoadingOverall } = useRoRacksContext();
  const isLoadingFinal = loading ?? isLoadingOverall;

  const title =
    pass === "firstPass" ? "1st Pass RO Quality" : "2nd Pass RO Quality";

  return (
    <div className="mt-4 min-h-[120px] rounded-2xl border border-gray-200 bg-white px-6 py-5">
      <h3 className="mb-6 px-12 text-xl font-bold text-gray-800">{title}</h3>

      {isLoadingFinal ? (
        <p className="py-4 text-center text-gray-400">Loading...</p>
      ) : Object.keys(cards).length === 0 ? (
        <p className="py-4 text-center text-gray-400">No data available</p>
      ) : (
        <div className="flex flex-col flex-wrap gap-3 px-12 md:flex-row">
          {Object.entries(cards).map(([key, { value, unit }]) => (
            <div
              key={key}
              className="flex min-w-[150px] flex-1 items-center justify-between rounded-xl bg-gray-50 px-6 py-4"
            >
              <p className="text-sm font-medium text-gray-700">
                {formatRoKey(key)} {/* ✅ Only this line changed */}
              </p>
              <div className="flex items-baseline gap-1">
                <span className="text-2xl font-bold text-green-500">
                  {value}
                </span>
                {unit && (
                  <span className="text-xs font-normal text-gray-500">
                    {unit}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RoQualityCards;
