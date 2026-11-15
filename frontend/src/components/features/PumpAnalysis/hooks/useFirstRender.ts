import { useRef } from "react";

export const useFirstRender = () => {
  const isFirstRender = useRef(true);

  if (isFirstRender.current) {
    isFirstRender.current = false;
    return true;
  }

  return false;
};
