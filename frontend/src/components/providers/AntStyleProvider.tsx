"use client";

import React, { FC, ReactNode } from "react";
import { px2remTransformer, StyleProvider } from "@ant-design/cssinjs";

const px2rem = px2remTransformer({ rootValue: 16 }); // 32px = 1rem

const AntStyleProvider: FC<{ children: ReactNode }> = ({ children }) => {
  return <StyleProvider transformers={[px2rem]}>{children} </StyleProvider>;
};

export default AntStyleProvider;
