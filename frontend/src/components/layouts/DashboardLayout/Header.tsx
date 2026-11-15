"use client";

import { ReactNode } from "react";
import { cn } from "../../../utils";

interface HeaderProps {
  children: ReactNode;
  className?: string;
}

// Simplified header - platform title and user menu moved to sidebar
const Header: React.FC<HeaderProps> = ({ children, className }) => {
  return (
    <div
      className={cn(
        "!bg-bg-base border-b-border-secondary !sticky !top-0 !z-50 h-[56px] w-full border-b-1 px-16 py-6",
        className
      )}
    >
      {children}
    </div>
  );
};

export default Header;
