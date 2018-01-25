# This is just some notes that I will take to help me with development

Event data from **cal_listhead()**:
    Title
    Start Date
    End Date
    Recurrence
    Label
    Description
    Reference

Info for one event, from **listshow_event(event)**:
% converttext(event['title'])
% formatcfgdatetime(event['startdate'], event['starttime'])
% formatcfgdatetime(event['enddate'], event['endtime'])
% recur_desc
% showReferPageParsedForLabel(event['label'])
% converttext(event['description'])
% showReferPageParsed(event, 'refer')
