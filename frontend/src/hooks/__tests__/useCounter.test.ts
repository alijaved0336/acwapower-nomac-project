import { renderHook, act } from "@testing-library/react";
import { useCounter } from "../useCounter";

describe("useCounter", () => {
  it("should initialize with default value of 0", () => {
    const { result } = renderHook(() => useCounter());

    expect(result.current.count).toBe(0);
  });

  it("should initialize with provided initial value", () => {
    const initialValue = 5;
    const { result } = renderHook(() => useCounter(initialValue));

    expect(result.current.count).toBe(initialValue);
  });

  it("should increment count", () => {
    const { result } = renderHook(() => useCounter(0));

    act(() => {
      result.current.increment();
    });

    expect(result.current.count).toBe(1);
  });

  it("should decrement count", () => {
    const { result } = renderHook(() => useCounter(5));

    act(() => {
      result.current.decrement();
    });

    expect(result.current.count).toBe(4);
  });

  it("should reset count to initial value", () => {
    const initialValue = 10;
    const { result } = renderHook(() => useCounter(initialValue));

    // Change the count
    act(() => {
      result.current.increment();
      result.current.increment();
    });

    expect(result.current.count).toBe(12);

    // Reset the count
    act(() => {
      result.current.reset();
    });

    expect(result.current.count).toBe(initialValue);
  });

  it("should handle multiple operations correctly", () => {
    const { result } = renderHook(() => useCounter(0));

    act(() => {
      result.current.increment(); // 1
      result.current.increment(); // 2
      result.current.decrement(); // 1
      result.current.increment(); // 2
    });

    expect(result.current.count).toBe(2);
  });

  it("should maintain function references between renders", () => {
    const { result, rerender } = renderHook(() => useCounter(0));

    const { increment, decrement, reset } = result.current;

    rerender();

    expect(result.current.increment).toBe(increment);
    expect(result.current.decrement).toBe(decrement);
    expect(result.current.reset).toBe(reset);
  });
});
