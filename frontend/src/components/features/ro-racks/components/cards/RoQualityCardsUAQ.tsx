"use client";

import React, { FC } from "react";
import { useRoRacksContext } from "../../context/RoRacksContext";
import { formatRoKey } from "@/components/features/ro-racks/utils/roRacksUtils";

type CardItem = { value: number | string; unit?: string };

type Props = {
  pass: "firstPass" | "secondPass";
  cards: Record<string, CardItem>;
  loading?: boolean;
};

const streamNames = ["Stream1", "Stream2", "Stream3"];
const streamBackgrounds: Record<string, string> = {
  Stream1: "#F0F0F0",
  Stream2: "#ECF6FE",
  Stream3: "#DEF8EA",
};

const RoQualityCardsUAQ: FC<Props> = ({ pass, cards, loading }) => {
  const { isLoadingOverall } = useRoRacksContext();
  const isLoadingFinal = loading ?? isLoadingOverall;

  const titleBase =
    pass === "firstPass" ? "1st Pass RO Quality" : "2nd Pass RO Quality";

  // Separate cards by stream
  const streamCards: Record<
    string,
    Record<string, CardItem>
  > = streamNames.reduce(
    (acc, stream) => {
      acc[stream] = Object.fromEntries(
        Object.entries(cards).filter(([key]) =>
          key.toLowerCase().includes(stream.toLowerCase())
        )
      );
      return acc;
    },
    {} as Record<string, Record<string, CardItem>>
  );

  return (
    <div className="mt-4 rounded-2xl bg-white px-8 py-6 shadow-sm">
      {/* Main Title */}
      <h2 className="mb-8 px-12 text-2xl font-bold text-gray-900">
        {titleBase}
      </h2>

      {/* Streams */}
      <div className="space-y-8">
        {streamNames.map((stream) => {
          const streamData = streamCards[stream];
          const hasData = Object.keys(streamData).length > 0;
          const bgColor = streamBackgrounds[stream];

          return (
            <div
              key={stream}
              className="rounded-2xl border border-gray-200 px-6 py-5 shadow-sm"
              style={{ backgroundColor: bgColor }}
            >
              <h3 className="mb-3 px-12 text-lg font-semibold text-gray-800">
                {stream.replace("Stream", "Stream ")}
              </h3>

              {isLoadingFinal ? (
                <p className="py-4 text-center text-gray-400">Loading...</p>
              ) : !hasData ? (
                <p className="py-4 text-center text-gray-400">
                  No data available
                </p>
              ) : (
                <div className="flex flex-col flex-wrap gap-3 px-12 md:flex-row">
                  {Object.entries(streamData).map(([key, { value, unit }]) => (
                    <div
                      key={key}
                      className="flex min-w-[150px] flex-1 items-center justify-between rounded-xl bg-white px-6 py-4"
                    >
                      <p className="text-sm font-medium text-gray-700">
                        {formatRoKey(key)}
                      </p>
                      <div className="flex items-baseline gap-1">
                        <span className="text-2xl font-bold text-green-600">
                          {value}
                        </span>
                        {unit && (
                          <span className="text-xs text-gray-500">{unit}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default RoQualityCardsUAQ;
