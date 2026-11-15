"use client";

import React, { FC } from "react";

// ✅ Updated to allow string | number
type CardItem = { value: number | string; unit: string; percent?: number };

type Props = {
  pass: "firstPass" | "secondPass";
  cards: Record<string, CardItem>;
  loading?: boolean;
};

const RoRacksCardsUAQ: FC<Props> = ({ cards, pass, loading }) => {
  const streamNames = ["Stream1", "Stream2", "Stream3"];

  // Prepare cards with merged Percent keys
  const preparedCards = Object.entries(cards).reduce<
    Record<string, { value: number | string; unit: string; percent: number }>
  >((acc, [key, item]) => {
    const lowerKey = key.toLowerCase();

    // Handle percent merging
    if (lowerKey.includes("percent")) {
      const mainKey = key.replace(/ percent$/i, "");
      if (acc[mainKey]) {
        // ✅ Handle string values for percent
        acc[mainKey].percent = typeof item.value === "number" ? item.value : 0;
      }
    } else {
      acc[key] = { ...item, percent: item.percent ?? 0 };
    }
    return acc;
  }, {});

  // Group by Stream
  const streamCards: Record<
    string,
    Record<string, CardItem>
  > = streamNames.reduce(
    (acc, stream) => {
      const entries = Object.entries(preparedCards).filter(([key]) =>
        key.toLowerCase().includes(stream.toLowerCase())
      );
      acc[stream] = Object.fromEntries(entries);
      return acc;
    },
    {} as Record<string, Record<string, CardItem>>
  );

  // Format key text
  const formatKey = (key: string) => {
    return key
      .replace(/Stream\d+/i, "")
      .replace(/([a-z])([A-Z])/g, "$1 $2")
      .replace(/\s+/g, " ")
      .trim()
      .split(" ")
      .map((word) =>
        word.length <= 2
          ? word.toUpperCase()
          : word.charAt(0).toUpperCase() + word.slice(1)
      )
      .join(" ");
  };

  // Background color logic (same as your existing file)
  const getBackgroundColor = (key: string) => {
    const lowerKey = key.toLowerCase();

    if (pass === "firstPass") {
      if (lowerKey.includes("permeate")) return "#ECF6FE";
      if (lowerKey.includes("sec")) return "#DEF8EA";
    } else {
      if (lowerKey.includes("permeate")) return "#F0F4FF";
      if (lowerKey.includes("sec")) return "#FFEBF2";
    }

    return "#F9FAFB";
  };

  return (
    <div className="mb-4 flex flex-col gap-6">
      {streamNames.map((stream) => {
        const cardsForStream = streamCards[stream];
        const cardEntries = Object.entries(cardsForStream);

        if (cardEntries.length === 0) return null;

        return (
          <div key={stream}>
            <h3 className="mb-3 text-lg font-bold text-gray-800">
              {stream.replace("Stream", "Stream ")}
            </h3>
            <div className="grid grid-cols-2 gap-3">
              {cardEntries.map(([key, { value, unit, percent = 0 }]) => (
                <div
                  key={key}
                  style={{ backgroundColor: getBackgroundColor(key) }}
                  className="flex items-center justify-between rounded-2xl px-6 py-5 shadow-sm"
                >
                  <p className="text-lg font-bold text-gray-700">
                    {formatKey(key)}
                  </p>
                  <p className="text-lg font-bold text-gray-800">
                    {value} {unit}{" "}
                    <span className="font-medium text-gray-500">
                      ({percent}%)
                    </span>
                  </p>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default RoRacksCardsUAQ;
