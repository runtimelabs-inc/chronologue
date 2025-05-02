import ChatPanel from '@/components/ChatPanel';
import CalendarPanel from '@/components/CalendarPanel';

export default function CalendarCopilotPage() {
  return (
    <div className="flex flex-col lg:flex-row h-screen w-full bg-gray-50">
      <div className="w-full lg:w-1/3 border-r border-gray-200">
        <ChatPanel />
      </div>
      <div className="w-full lg:w-2/3">
        <CalendarPanel />
      </div>
    </div>
  );
}
