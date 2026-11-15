import { Skeleton } from "antd";
import React from "react";

const SkeletonSection = () => {
  return (
    <>
      <Skeleton.Input
        active
        block
        size="default"
        style={{
          width: "100%", // 100% of parent cell
          minWidth: "unset",
          maxWidth: "100%", // never exceed
          boxSizing: "border-box", // include padding/border in width
        }}
      />

      <Skeleton.Input
        active
        block
        size="default"
        style={{
          width: "100%", // half of parent cell
          maxWidth: "100%",
          minWidth: "unset",
          boxSizing: "border-box",
        }}
      />

      <Skeleton.Input
        active
        block
        size="default"
        style={{
          width: "100%", // 100% of parent cell
          minWidth: "unset",
          maxWidth: "100%", // never exceed
          boxSizing: "border-box", // include padding/border in width
        }}
      />

      <Skeleton.Input
        active
        block
        size="default"
        style={{
          width: "100%", // half of parent cell
          maxWidth: "100%",
          minWidth: "unset",
          boxSizing: "border-box",
        }}
      />
    </>
  );
};

export default SkeletonSection;
