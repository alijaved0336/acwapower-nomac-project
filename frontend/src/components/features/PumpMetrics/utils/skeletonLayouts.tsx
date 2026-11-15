"use client";
import { theme } from "antd";
import { useAppSelector } from "@/hooks";
import Spinner from "@/components/common/Spinner";

export const PumpMetricsSpinner = () => {
  const { token } = theme.useToken();
  const mode = useAppSelector((state) => state.settings.mode);
  const isDark = mode === "dark";

  return (
    <div className="relative mt-8 grid h-[calc(100vh-68px)] grow grid-cols-4 grid-rows-[1fr_min-content_1fr] gap-8 p-8">
      {/* Main HPP Pump Chart */}
      <div
        className="relative col-span-4"
        style={{
          borderRadius: "12px",
          border: `1px solid ${token.colorBorder}`,
          boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
          background: token.colorBgContainer,
          height: "100%",
        }}
      >
        <div
          className="absolute inset-0 flex items-center justify-center"
          style={{ backgroundColor: token.colorBgMask }}
        >
          <Spinner />
        </div>
      </div>

      {/* KPIs Row Title */}
      <div className="col-span-4 h-min">
        <h2
          className="px-12 font-[Figtree] text-[16px] leading-[32px] font-semibold"
          style={{ color: token.colorText }}
        >
          KPIs Comparison
        </h2>
      </div>

      {/* 4 KPI Cards */}
      {[
        {
          border: `1px solid ${token.colorBorder}`,
          background: token.colorBgContainer,
        },
        {
          border: `1px solid ${token.colorBorder}`,
          background: token.colorBgContainer,
        },
        {
          border: `1px solid ${token.colorBorder}`,
          background: token.colorBgContainer,
        },
        {
          border: `1px solid ${token.colorBorder}`,
          background: token.colorBgContainer,
        },
      ].map((style, index) => (
        <div
          key={index}
          className="relative"
          style={{
            borderRadius: "12px",
            ...style,
            height: "100%",
          }}
        >
          <div
            className="absolute inset-0 flex items-center justify-center"
            style={{ backgroundColor: token.colorBgMask }}
          >
            <Spinner />
          </div>
        </div>
      ))}
    </div>
  );
};
