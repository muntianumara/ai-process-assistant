# IT Incident Reporting Procedure

| Document ID | Version | Effective date | Owner |
|---|---|---|---|
| IT-PRO-012 | 3.0 | 1 March 2026 | IT Service Desk, Contoso Business Services |

## 1. Purpose and scope

An **incident** is any unplanned interruption or loss of quality of an IT service
(for example: your laptop does not start, Outlook does not open, the network is down).
This procedure explains how to report incidents and how quickly IT will respond.

Requests for **new** hardware, software or access rights are *service requests*, not incidents.
They are handled through the *IT Service Catalogue* and are not covered by this procedure.

## 2. How to report an incident

Use one of the following channels:

| Channel | Address | When to use it |
|---|---|---|
| IT Service Portal (preferred) | `https://itsupport.contoso-bs.example` | All incidents |
| E-mail | `itsupport@contoso-bs.example` | All incidents; a ticket is created automatically |
| Phone | Internal extension **3100** | Only for P1/P2 incidents, or if you cannot access the portal or e-mail |

Every report must include:
1. your name and department;
2. the **asset tag** of the affected device (sticker on the device, format `CBS-LT-00000`);
3. a short description of the problem and when it started;
4. the exact error message or a screenshot;
5. how many people are affected.

You receive a ticket number (format `INC-2026-000000`) by e-mail. Use it in all further communication.

## 3. Priority levels and response times

The IT Service Desk assigns the priority based on impact and urgency.

| Priority | Description | Example | First response | Target resolution |
|---|---|---|---|---|
| **P1 – Critical** | A whole department or site cannot work, or a security incident | E-mail down for everyone; stolen laptop | 15 minutes | 4 hours |
| **P2 – High** | A team or a business-critical application is affected | The SAP system is unavailable for the Finance team | 30 minutes | 8 business hours |
| **P3 – Medium** | One user cannot work normally and has no workaround | Your laptop does not start | 4 business hours | 3 business days |
| **P4 – Low** | Minor issue, a workaround exists | A printer on your floor is out of order | 1 business day | 10 business days |

Business hours are Monday to Friday, 08:00–18:00. **P1 incidents are handled 24/7.**

## 4. Security incidents

- **Phishing / suspicious e-mail:** do not click any link or open attachments. Use the
  *Report Phishing* button in Outlook or forward the e-mail to `security@contoso-bs.example`.
- **Lost or stolen device:** report it **within 1 hour** by phone (extension 3100).
  Lost or stolen devices are always treated as **P1**.
- Never try to investigate a security incident on your own.

## 5. Escalation

If you do not receive a first response within the target time:
1. reply to the ticket e-mail with the word **ESCALATE** in the subject;
2. if there is still no response after **2 hours**, contact the IT Service Desk Team Lead at
   `it.lead@contoso-bs.example`.

## 6. Closing a ticket

When the issue is fixed, the ticket status changes to *Resolved*. You have **5 business days**
to confirm the solution or reopen the ticket. After that, the ticket is closed automatically
and you receive a short satisfaction survey.
