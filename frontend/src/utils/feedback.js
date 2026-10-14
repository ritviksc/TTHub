export const FEEDBACK_SPEAKERS = {
  'kaumātua': 'Kaumātua', kaimahi: 'Kaimahi', 'whānau': 'Whānau', unknown: 'Unknown',
}

export function feedbackSpeakerLabel(value) {
  return value === 'participant' ? 'Kaumātua' : FEEDBACK_SPEAKERS[value] || 'Unknown'
}
