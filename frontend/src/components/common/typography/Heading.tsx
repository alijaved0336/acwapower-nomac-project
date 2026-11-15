import React, { FC, HTMLProps, ReactNode } from "react";
import { cn } from "@/utils/cn";

type HeadingProps = HTMLProps<HTMLHeadingElement> & {
  children: ReactNode;
  level: 1 | 2 | 3 | 4 | 5 | 6;
};

const Heading: FC<HeadingProps> = ({ children, className, level, ...rest }) => {
  const headings = {
    1: (
      <h1
        className={cn("text-text-base text-4xl font-normal", className)}
        {...rest}
      >
        {children}
      </h1>
    ),
    2: (
      <h2
        className={cn("text-text-base text-[2rem] font-normal", className)}
        {...rest}
      >
        {children}
      </h2>
    ),
    3: (
      <h3
        className={cn("text-text-base text-3xl font-normal", className)}
        {...rest}
      >
        {children}
      </h3>
    ),
    4: (
      <h4
        className={cn("text-text-base text-2xl font-normal", className)}
        {...rest}
      >
        {children}
      </h4>
    ),
    5: (
      <h5
        className={cn("text-text-base text-xl font-normal", className)}
        {...rest}
      >
        {children}
      </h5>
    ),
    6: (
      <h6
        className={cn("text-text-base text-lg font-normal", className)}
        {...rest}
      >
        {children}
      </h6>
    ),
  };
  return headings[level];
};

export default Heading;
