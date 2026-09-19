import type { Meta, StoryObj } from "@storybook/react-vite";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BookingArtifactScanner } from "../features/inbox/BookingArtifactScanner";
import { V10LiveExecutionPanel } from "../features/execution/V10LiveExecutionPanel";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const panelMeta = {
  title: "V10/Live execution panel",
  component: V10LiveExecutionPanel,
  decorators: [
    (Story) => (
      <QueryClientProvider client={queryClient}>
        <div style={{ maxWidth: 720, margin: "2rem auto", padding: "1rem" }}>
          <Story />
        </div>
      </QueryClientProvider>
    ),
  ],
} satisfies Meta<typeof V10LiveExecutionPanel>;

export default panelMeta;
type PanelStory = StoryObj<typeof panelMeta>;

export const Ready: PanelStory = {
  args: { journeyId: "demo-journey" },
};

export const InboxScanner: StoryObj<typeof BookingArtifactScanner> = {
  render: () => (
    <div style={{ maxWidth: 560, margin: "2rem auto", padding: "1rem" }}>
      <BookingArtifactScanner />
    </div>
  ),
};
