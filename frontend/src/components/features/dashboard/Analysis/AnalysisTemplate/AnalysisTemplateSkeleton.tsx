import React from "react";
import { Card, Skeleton } from "antd";

const AnalysisTemplateSkeleton = () => {
  return (
    <div className="!space-y-12">
      {/* Render 2 skeleton widget cards */}
      {Array.from({ length: 2 }).map((_, index) => (
        <Card key={index} className="card relative">
          <div className="mb-3 flex justify-end gap-12">
            <Skeleton.Button
              style={{ minWidth: 32, width: "100%", height: 32 }}
            />
            <Skeleton.Button
              style={{ minWidth: 32, width: "100%", height: 32 }}
            />
            <Skeleton.Button
              style={{ minWidth: 32, width: "100%", height: 32 }}
            />
            <Skeleton.Button
              style={{ minWidth: 32, width: "100%", height: 32 }}
            />
          </div>
          <Skeleton.Input
            style={{ minHeight: "36vh", width: "100%" }}
            active
            block
          />
        </Card>
      ))}
    </div>
  );
};

export default AnalysisTemplateSkeleton;
