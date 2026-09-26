# Physical Testing

```Client Response
ACC as the main funder currently only want to know if
physical testing has been completed in a particular
Term/Quarter or not, i.e. YES/NO.
However, kaimahi will want to be able to compare
testing from quarter to quarter to be able to show
kaumātua. Refer to Admin 4 and 4a in the Dropbox.
Most kapa will be doing this by showing kaumātua the
hard copy page with the results. However, some kapa
have developed Excel spreadsheets with graphs.
Being able to show kaumātua the data/graphs in the
platform would be beneficial.
```

## Taurite Tū Physical Tests

* Timed up and go (3 meters)
* Sit to stand to (30 seconds)
* 4 Point Balance Tests:
    * Feet together
    * Half step
    * Heel to toe
    * One foot


## Design Flow

For each kaumātua, show:
- Testing completed: Yes/No — whether they have at least one completed assessment within the selected dates.
- Number of completed assessments within that range.
- Recorded measurements and changes between assessments, where comparable results exist.
Across the selected branch or branches, show the number of eligible participants, how many completed testing, the completion percentage, and the total completed assessments. Someone with no assessment must still appear as No—so reporting starts from the participant list, not just existing test records.
Django should calculate the statistics and changes. The LLM then explains those supplied figures, without diagnosing participants or claiming that the programme caused an improvement. We use reuse celery approach as well.

