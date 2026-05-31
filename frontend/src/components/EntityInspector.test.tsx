import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EntityInspector } from "./EntityInspector";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const mockEntity = {
  id: "entity-1",
  type: "Domain" as const,
  value: "example.com",
  properties: {},
  tags: [] as string[],
  notes: "",
  source: "manual",
  origin_source: "manual",
  weight: 1,
  icon: "globe",
  project_id: "project-1",
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

const mockState = {
  selectedNodeId: "entity-1",
  selectedEdgeId: null,
  entities: new Map([["entity-1", mockEntity]]),
  edges: new Map(),
  removeEntity: vi.fn(),
  removeEdge: vi.fn(),
  updateEdge: vi.fn(),
  selectNode: vi.fn(),
  selectEdge: vi.fn(),
};

vi.mock("../stores/graphStore", () => ({
  useGraphStore: Object.assign(vi.fn(() => mockState), {
    getState: vi.fn(() => mockState),
    setState: vi.fn(),
  }),
}));

vi.mock("../stores/projectStore", () => ({
  useProjectStore: vi.fn(() => ({
    currentProject: { id: "project-1", name: "Test" },
  })),
}));

vi.mock("../hooks/useIsViewer", () => ({
  useIsViewer: vi.fn(() => false),
}));

const { mockUpdate, mockToastError } = vi.hoisted(() => ({
  mockUpdate: vi.fn(),
  mockToastError: vi.fn(),
}));

vi.mock("../api/client", () => ({
  api: {
    transforms: { forEntity: vi.fn().mockResolvedValue([]) },
    entities: { update: mockUpdate },
  },
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: mockToastError },
}));

function renderInspector() {
  const container = document.createElement("div");
  document.body.appendChild(container);
  const root: Root = createRoot(container);
  act(() => {
    root.render(<EntityInspector />);
  });
  return {
    container,
    unmount: () => {
      act(() => root.unmount());
      container.remove();
    },
  };
}

describe("EntityInspector — entity rename", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("clicking the value text shows an input pre-filled with current value", async () => {
    const { container, unmount } = renderInspector();

    const valueEl = container.querySelector("[data-testid='entity-value']") as HTMLElement;
    expect(valueEl).toBeTruthy();
    expect(valueEl.textContent).toBe("example.com");

    act(() => { valueEl.click(); });

    const input = container.querySelector("[data-testid='entity-value-input']") as HTMLInputElement;
    expect(input).toBeTruthy();
    expect(input.value).toBe("example.com");

    unmount();
  });

  it("pressing Escape cancels rename without calling the API", async () => {
    const { container, unmount } = renderInspector();

    const valueEl = container.querySelector("[data-testid='entity-value']") as HTMLElement;
    act(() => { valueEl.click(); });

    const input = container.querySelector("[data-testid='entity-value-input']") as HTMLInputElement;

    // First type something so onBlur would save if not guarded
    const nativeInputSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
    act(() => {
      nativeInputSetter?.call(input, "should-not-be-saved.com");
      input.dispatchEvent(new Event("input", { bubbles: true }));
    });

    await act(async () => {
      input.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
      input.dispatchEvent(new Event("blur", { bubbles: true }));
    });

    expect(container.querySelector("[data-testid='entity-value-input']")).toBeNull();
    expect(mockUpdate).not.toHaveBeenCalled();

    unmount();
  });

  it("typing a new value and pressing Enter calls api.entities.update", async () => {
    mockUpdate.mockResolvedValueOnce({ ...mockEntity, value: "renamed.com" });
    const { container, unmount } = renderInspector();

    const valueEl = container.querySelector("[data-testid='entity-value']") as HTMLElement;
    act(() => { valueEl.click(); });

    const input = container.querySelector("[data-testid='entity-value-input']") as HTMLInputElement;
    const nativeInputSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
    act(() => {
      nativeInputSetter?.call(input, "renamed.com");
      input.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await act(async () => {
      input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
    });

    expect(mockUpdate).toHaveBeenCalledWith("project-1", "entity-1", { value: "renamed.com" });

    unmount();
  });

  it("shows a toast error when the API returns a conflict message", async () => {
    mockUpdate.mockRejectedValueOnce(new Error("An entity with that value already exists"));
    const { container, unmount } = renderInspector();

    const valueEl = container.querySelector("[data-testid='entity-value']") as HTMLElement;
    act(() => { valueEl.click(); });

    const input = container.querySelector("[data-testid='entity-value-input']") as HTMLInputElement;
    const nativeInputSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")?.set;
    act(() => {
      nativeInputSetter?.call(input, "second.com");
      input.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await act(async () => {
      input.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
    });

    expect(mockToastError).toHaveBeenCalledWith(
      expect.stringContaining("An entity with that value already exists")
    );

    unmount();
  });
});
