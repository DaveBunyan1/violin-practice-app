export type NoteValue = "whole" | "half" | "quarter" | "eighth" | "sixteenth";

export type MusicalNote = {
  pitch: string;
  value: NoteValue;
  isRest?: boolean;
};

export const BEAT_VALUES: Record<NoteValue, number> = {
  whole: 4,
  half: 2,
  quarter: 1,
  eighth: 0.5,
  sixteenth: 0.25,
};
