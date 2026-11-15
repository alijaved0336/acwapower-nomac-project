import { ApexOptions } from "apexcharts";
import { ApexChartTheme } from "@/types/apex-charts";

// Default color palettes
export const APEX_COLOR_PALETTES = {
  primary: [
    "#008FFB",
    "#00E396",
    "#FEB019",
    "#FF4560",
    "#775DD0",
    "#546E7A",
    "#26A69A",
    "#D10CE8",
  ],
  secondary: [
    "#3F51B5",
    "#4CAF50",
    "#FF9800",
    "#F44336",
    "#9C27B0",
    "#607D8B",
    "#009688",
    "#E91E63",
  ],
  success: [
    "#00E396",
    "#00D09C",
    "#00BF63",
    "#00AC2B",
    "#009900",
    "#008500",
    "#007200",
    "#005E00",
  ],
  warning: [
    "#FEB019",
    "#FFB300",
    "#FF8F00",
    "#FF6F00",
    "#E65100",
    "#D84315",
    "#BF360C",
    "#A6360C",
  ],
  error: [
    "#FF4560",
    "#F44336",
    "#E53935",
    "#D32F2F",
    "#C62828",
    "#B71C1C",
    "#AD1457",
    "#880E4F",
  ],
  info: [
    "#008FFB",
    "#2196F3",
    "#1976D2",
    "#1565C0",
    "#0D47A1",
    "#01579B",
    "#006064",
    "#004D40",
  ],
} as const;

// Light theme configuration
export const LIGHT_THEME: ApexChartTheme = {
  mode: "light",
  palette: "palette1",
  colors: [...APEX_COLOR_PALETTES.primary],
  background: "#ffffff",
  foreColor: "#373d3f",
  fontFamily:
    "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  fontSize: "14px",
};

// Dark theme configuration
export const DARK_THEME: ApexChartTheme = {
  mode: "dark",
  palette: "palette1",
  colors: [...APEX_COLOR_PALETTES.primary],
  background: "#1a202c",
  foreColor: "#f7fafc",
  fontFamily:
    "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  fontSize: "14px",
};

// Base chart options that apply to all charts
export const BASE_CHART_OPTIONS: Partial<ApexOptions> = {
  chart: {
    fontFamily:
      "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    toolbar: {
      show: true,
      offsetX: 0,
      offsetY: 0,
      tools: {
        download: true,
        selection: true,
        zoom: true,
        zoomin: true,
        zoomout: true,
        pan: true,
        reset: true,
      },
      export: {
        csv: {
          filename: "chart-data",
          columnDelimiter: ",",
          headerCategory: "category",
          headerValue: "value",
        },
        svg: {
          filename: "chart",
        },
        png: {
          filename: "chart",
        },
      },
    },
    animations: {
      enabled: true,
      speed: 800,
      animateGradually: {
        enabled: true,
        delay: 150,
      },
      dynamicAnimation: {
        enabled: true,
        speed: 350,
      },
    },
    background: "transparent",
    foreColor: "#373d3f",
  },
  xaxis: {
    labels: {
      datetimeFormatter: {
        year: "yy",
        month: "MM/yy",
        day: "dd/MM/yy",
        hour: "dd/MM/yy HH:mm",
      },
    },
  },
  dataLabels: {
    enabled: false,
  },
  stroke: {
    curve: "smooth",
    width: 2,
  },
  grid: {
    show: true,
    borderColor: "#e2e8f0",
    strokeDashArray: 0,
    position: "back" as const,
    xaxis: {
      lines: {
        show: false,
      },
    },
    yaxis: {
      lines: {
        show: true,
      },
    },
    row: {
      colors: undefined,
      opacity: 0.5,
    },
    column: {
      colors: undefined,
      opacity: 0.5,
    },
    // padding: {
    //   top: 0,
    //   right: 0,
    //   bottom: 0,
    //   left: 0,
    // },
  },
  tooltip: {
    enabled: true,
    shared: true,
    followCursor: false,
    intersect: false,
    inverseOrder: false,
    fillSeriesColor: false,
    theme: "light",
    style: {
      fontSize: "12px",
      fontFamily:
        "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    },
    onDatasetHover: {
      highlightDataSeries: false,
    },
    x: {
      show: true,
      format: "dd MMM",
      formatter: undefined,
    },
    y: {
      formatter: undefined,
      title: {
        formatter: (seriesName: string) => seriesName,
      },
    },
    marker: {
      show: true,
    },
  },
  legend: {
    show: true,
    position: "bottom" as const,
    horizontalAlign: "center" as const,
    floating: false,
    fontSize: "14px",
    fontFamily:
      "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    fontWeight: 400,
    formatter: undefined,
    inverseOrder: false,
    width: undefined,
    height: undefined,
    tooltipHoverFormatter: undefined,
    customLegendItems: [],
    offsetX: 0,
    offsetY: 0,
    labels: {
      colors: undefined,
      useSeriesColors: false,
    },
    markers: {
      size: 8,
      strokeWidth: 0,
      fillColors: undefined,
      customHTML: undefined,
      onClick: undefined,
      offsetX: 0,
      offsetY: 0,
    },
    itemMargin: {
      horizontal: 5,
      vertical: 0,
    },
    onItemClick: {
      toggleDataSeries: true,
    },
    onItemHover: {
      highlightDataSeries: true,
    },
  },
  responsive: [
    {
      breakpoint: 768,
      options: {
        chart: {
          toolbar: {
            show: false,
          },
        },
        legend: {
          position: "bottom" as const,
        },
      },
    },
    {
      breakpoint: 480,
      options: {
        chart: {
          toolbar: {
            show: false,
          },
        },
        legend: {
          show: false,
        },
      },
    },
  ],
};

// Theme-specific options
export const getThemeOptions = (
  theme: "light" | "dark"
): Partial<ApexOptions> => {
  const themeConfig = theme === "dark" ? DARK_THEME : LIGHT_THEME;

  return {
    theme: {
      mode: themeConfig.mode,
      palette: themeConfig.palette,
    },
    chart: {
      background: themeConfig.background,
      foreColor: themeConfig.foreColor,
    },
    grid: {
      borderColor: theme === "dark" ? "#2d3748" : "#e2e8f0",
    },
    tooltip: {
      theme: themeConfig.mode,
    },
    legend: {
      labels: {
        colors: themeConfig.foreColor,
      },
    },
  };
};

// Merge options utility
export const mergeChartOptions = (
  baseOptions: Partial<ApexOptions>,
  themeOptions: Partial<ApexOptions>,
  customOptions?: Partial<ApexOptions>
): ApexOptions => {
  // Deep merge function

  const deepMerge = (target: any, source: any): any => {
    const result = { ...target };

    for (const key in source) {
      if (
        source[key] &&
        typeof source[key] === "object" &&
        !Array.isArray(source[key])
      ) {
        result[key] = deepMerge(result[key] || {}, source[key]);
      } else {
        result[key] = source[key];
      }
    }

    return result;
  };

  let merged = deepMerge(baseOptions, themeOptions);

  if (customOptions) {
    merged = deepMerge(merged, customOptions);
  }

  return merged as ApexOptions;
};

// Chart type specific options
export const CHART_TYPE_OPTIONS = {
  bar: {
    chart: {
      type: "bar" as const,
    },
    plotOptions: {
      bar: {
        horizontal: false,
        columnWidth: "55%",
        endingShape: "rounded",
        borderRadius: 2,
      },
    },
  },
  line: {
    chart: {
      type: "line" as const,
    },
    stroke: {
      curve: "smooth" as const,
      width: 3,
    },
    markers: {
      size: 4,
      colors: undefined,
      strokeColors: "#fff",
      strokeWidth: 2,
      hover: {
        size: 7,
      },
    },
  },
  area: {
    chart: {
      type: "area" as const,
    },
    stroke: {
      curve: "smooth" as const,
      width: 2,
    },
    fill: {
      type: "gradient",
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.7,
        opacityTo: 0.9,
        stops: [0, 90, 100],
      },
    },
  },
  pie: {
    chart: {
      type: "pie" as const,
    },
    plotOptions: {
      pie: {
        expandOnClick: false,
        donut: {
          size: "70%",
        },
      },
    },
  },
  donut: {
    chart: {
      type: "donut" as const,
    },
    plotOptions: {
      pie: {
        expandOnClick: false,
        donut: {
          size: "70%",
          background: "transparent",
        },
      },
    },
  },
  radialBar: {
    chart: {
      type: "radialBar" as const,
    },
    plotOptions: {
      radialBar: {
        offsetY: 0,
        startAngle: 0,
        endAngle: 270,
        hollow: {
          margin: 5,
          size: "30%",
          background: "transparent",
          image: undefined,
        },
        dataLabels: {
          name: {
            show: false,
          },
          value: {
            show: false,
          },
        },
      },
    },
  },
} as const;
