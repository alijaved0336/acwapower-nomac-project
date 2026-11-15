import { Spin } from "antd";
import React from "react";

const ChartSpinner = () => {
  return (
    <div
      className="dark:bg-bg-container/60 absolute top-0 left-0 z-50 flex h-full w-full items-center justify-center"
      style={{
        backdropFilter: "blur(2px)",
      }}
    >
      <Spin />
    </div>
  );
};

export default ChartSpinner;
