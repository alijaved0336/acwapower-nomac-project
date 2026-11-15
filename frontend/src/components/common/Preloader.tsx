"use client";
import { useEffect } from "react";
import { store, slices } from "@/store/store";
type Slice = keyof typeof slices;
type Endpoint<T extends Slice> = keyof (typeof slices)[T]["endpoints"];
type PreloadSlice<T extends Slice> = {
  endpoint: Endpoint<T>;
  data: unknown;
  args?: unknown;
};
type PreloadProps<T extends Slice> = {
  slice: T;
} & PreloadSlice<T>;
function Preloader<T extends Slice>(props: PreloadProps<T>) {
  useEffect(() => {
    async function setDataToSlice() {
      const { endpoint, slice, data, args } = props;
      if (!endpoint) return;
      await store.dispatch(
        // @ts-expect-error – suppress TS2349 temporarily
        slices[slice].util.upsertQueryData(endpoint, args || undefined, data)
      );
    }
    setDataToSlice();
  }, [props]);
  return null;
}
export default Preloader;
