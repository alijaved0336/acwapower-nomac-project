export type TRecursiveNonNullable<T> = T extends object
  ? {
      [K in keyof T]: TRecursiveNonNullable<T[K]>;
    }
  : T;

export type TOption = { label: string; value: string; key: string };
