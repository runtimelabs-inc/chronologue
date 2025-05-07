// src/components/ChatPanel.tsx
import { useState, useContext } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { v4 as uuidv4 } from 'uuid';
import { Configuration, OpenAIApi } from 'openai';
import { CalendarEventContext } from '@/context/CalendarEventContext';

const configuration = new Configuration({
  apiKey: process.env.NEXT_PUBLIC_OPENAI_API_KEY,
});
const openai = new OpenAIApi(configuration);

export default function ChatPanel() {
  const [messages, setMessages] = useState<string[]>([]);
  const [input, setInput] = useState('');
  const [preview, setPreview] = useState<any | null>(null);
  const { addEvent } = useContext(CalendarEventContext);

  const handleSend = async () => {
    if (!input.trim()) return;
    setMessages([...messages, input]);

    const functions = [
      {
        name: 'create_event_trace',
        description: 'Create a structured event from a scheduling prompt',
        parameters: {
          type: 'object',
          properties: {
            title: { type: 'string' },
            timestamp: { type: 'string', format: 'date-time' },
            duration: { type: 'number' }
          },
          required: ['title', 'timestamp', 'duration'],
        },
      },
    ];

    const completion = await openai.createChatCompletion({
      model: 'gpt-4-0613',
      messages: [
        { role: 'system', content: 'You help schedule calendar events based on prompts.' },
        { role: 'user', content: input },
      ],
      functions,
      function_call: { name: 'create_event_trace' },
    });

    const fnCall = completion.data.choices[0].message?.function_call;
    if (fnCall?.name === 'create_event_trace') {
      const args = JSON.parse(fnCall.arguments || '{}');
      const trace = {
        id: uuidv4(),
        title: args.title,
        start: new Date(args.timestamp),
        end: new Date(new Date(args.timestamp).getTime() + args.duration * 60000),
      };
      setPreview(trace);
    }
    setInput('');
  };

  const handleConfirm = () => {
    if (preview) {
      addEvent(preview);
      setPreview(null);
    }
  };

  return (
    <div className="flex flex-col h-full p-4 gap-4 w-full max-w-md">
      <Card className="flex-1 overflow-y-auto rounded-2xl shadow-md bg-white">
        <CardContent className="p-4 space-y-3">
          {messages.map((msg, idx) => (
            <div key={idx} className="bg-gray-100 p-3 rounded-xl text-sm">
              {msg}
            </div>
          ))}
          {preview && (
            <div className="bg-blue-100 p-4 rounded-xl text-sm">
              <div><strong>Preview:</strong> {preview.title}</div>
              <div>{preview.start.toLocaleString()} – {preview.end.toLocaleString()}</div>
              <Button className="mt-2" onClick={handleConfirm}>Add to Calendar</Button>
            </div>
          )}
        </CardContent>
      </Card>
      <div className="flex gap-2">
        <Input
          className="flex-1 rounded-xl border-gray-300"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="e.g. Block 2 hours Friday for writing"
        />
        <Button onClick={handleSend}>Send</Button>
      </div>
    </div>
  );
} 


// src/components/CalendarPanel.tsx
import { useContext } from 'react';
import { Calendar, momentLocalizer } from 'react-big-calendar';
import moment from 'moment';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import { CalendarEventContext } from '@/context/CalendarEventContext';

const localizer = momentLocalizer(moment);

export default function CalendarPanel() {
  const { events } = useContext(CalendarEventContext);

  return (
    <div className="flex-1 p-4 bg-white rounded-2xl shadow-md">
      <Calendar
        localizer={localizer}
        events={events}
        startAccessor="start"
        endAccessor="end"
        style={{ height: '100%' }}
      />
    </div>
  );
}