"use client";

import React, { FC, memo, PropsWithChildren } from "react";

const ContentArea: FC<PropsWithChildren> = ({ children }) => {
  return (
    <div
      className="bg-blue-0 dark:bg-bg-container content-area-main relative overflow-y-auto"
      style={{
        width: "100%",
        height: "100vh",
        padding: 0,
        margin: 0,
      }}
    >
      {children}
    </div>
  );
};

export default memo(ContentArea);
