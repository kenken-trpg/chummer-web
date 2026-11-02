/** Matrix tests requested for the detailed VTT palette; pages refer to the Japanese core book. */
import type { UiFn } from "@/lib/i18n";
export type MatrixLimit = "attack" | "sleaze" | "dataprocessing" | "firewall";
export const MATRIX_ACTIONS: {
  name: string;
  skill: string;
  attribute: string;
  limit: MatrixLimit | null;
  label: Parameters<UiFn>[0];
}[] = [
  {
    name: "Brute Force",
    skill: "Cybercombat",
    attribute: "LOG",
    limit: "attack",
    label: "vtt.matrixAction0",
  },
  {
    name: "Check Overwatch Score",
    skill: "Electronic Warfare",
    attribute: "LOG",
    limit: "sleaze",
    label: "vtt.matrixAction1",
  },
  {
    name: "Crack File",
    skill: "Hacking",
    attribute: "LOG",
    limit: "attack",
    label: "vtt.matrixAction2",
  },
  {
    name: "Crash Program",
    skill: "Cybercombat",
    attribute: "LOG",
    limit: "attack",
    label: "vtt.matrixAction3",
  },
  {
    name: "Data Spike",
    skill: "Cybercombat",
    attribute: "LOG",
    limit: "attack",
    label: "vtt.matrixAction4",
  },
  {
    name: "Disarm Data Bomb",
    skill: "Software",
    attribute: "INT",
    limit: "firewall",
    label: "vtt.matrixAction5",
  },
  {
    name: "Edit File",
    skill: "Computer",
    attribute: "LOG",
    limit: "dataprocessing",
    label: "vtt.matrixAction6",
  },
  {
    name: "Erase Mark",
    skill: "Computer",
    attribute: "LOG",
    limit: "attack",
    label: "vtt.matrixAction7",
  },
  {
    name: "Format Device",
    skill: "Computer",
    attribute: "LOG",
    limit: "sleaze",
    label: "vtt.matrixAction8",
  },
  {
    name: "Hack on the Fly",
    skill: "Hacking",
    attribute: "LOG",
    limit: "sleaze",
    label: "vtt.matrixAction9",
  },
  {
    name: "Hide",
    skill: "Electronic Warfare",
    attribute: "INT",
    limit: "sleaze",
    label: "vtt.matrixAction10",
  },
  {
    name: "Jack Out",
    skill: "Hardware",
    attribute: "WIL",
    limit: "firewall",
    label: "vtt.matrixAction11",
  },
  {
    name: "Jam Signals",
    skill: "Electronic Warfare",
    attribute: "LOG",
    limit: "attack",
    label: "vtt.matrixAction12",
  },
  {
    name: "Jump Into Rigged Device",
    skill: "Electronic Warfare",
    attribute: "LOG",
    limit: "dataprocessing",
    label: "vtt.matrixAction13",
  },
  {
    name: "Matrix Perception",
    skill: "Computer",
    attribute: "INT",
    limit: "dataprocessing",
    label: "vtt.matrixAction14",
  },
  {
    name: "Matrix Search",
    skill: "Computer",
    attribute: "INT",
    limit: "dataprocessing",
    label: "vtt.matrixAction15",
  },
  {
    name: "Reboot Device",
    skill: "Computer",
    attribute: "LOG",
    limit: "dataprocessing",
    label: "vtt.matrixAction16",
  },
  {
    name: "Set Data Bomb",
    skill: "Software",
    attribute: "LOG",
    limit: "sleaze",
    label: "vtt.matrixAction17",
  },
  {
    name: "Snoop",
    skill: "Electronic Warfare",
    attribute: "INT",
    limit: "sleaze",
    label: "vtt.matrixAction18",
  },
  {
    name: "Spoof Command",
    skill: "Hacking",
    attribute: "INT",
    limit: "sleaze",
    label: "vtt.matrixAction19",
  },
  {
    name: "Trace Icon",
    skill: "Computer",
    attribute: "INT",
    limit: null,
    label: "vtt.matrixAction20",
  },
];
