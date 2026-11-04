"""
Request Issue(title, body)
 -> Made by application
 -> Received by our AI Service router
                                                               Send Request to AI Service
Repo 1  |User 1 (Updated Issue) -> Received by our app server   ------------------------
        |       -> Validation, Single-Transaction (Job Failrue)          |             | J1 : * Owner Token [Do Magic with it]              Assign jobs to workers (Claiming)
        |                                                                |             |      * Lease time  [How long can you have it?]         ===============                         |Worker 1|
        |                                                                |             ↓                                                        |             |                         |Worker 2|
        |                                                                | --->    AI Service ------------------------------------------------> |  Scheduler  | ------------------>     |Worker 3| ------------->
        |-> User 2 (Created Issue) -> Received by our app server         |             ↑                                                        |             |                         |Worker 4|
        |       -> Validation, Single-Transaction (Job Failrue)          |             | J2 : * Owner Token [Do Magic with it]                  |             |                         |Worker 5|
                                                                         |             |      * Lease time  [How long can you have it?]         ===============                         |Worker 6|
        |       -> Validation, Single-Transaction (Job Failrue) ------------------------                                                     Returning result to caller (Resolving)
        |-> User 3 (Created Issue)                             Send Request to AI Service


       -> If worker is sucessfully done:
            - Check DB a job with job_id and token
            - Validate the token and mark the job as done
                -> If the token of the job in the database and of the token sent by the AI service is not the same then mark that job as termianted
                   because this likely happened when the lease time expired and we scheduled another job with the same id
            - Save the result
       -> If worker is not done:
            - We can not know the cause (OpenAI Service failed, or the AI service itself crashed)
            - The only way we can tell is from the Application serivce we can check the DB to see if the lease time has expired
            - Resend the job with a different token but with the same id so that we can validate it later

Repo 2  |-> User 1 (Created Issue)
        |-> User 3 (Updated Issue)
        |-> User 4 (Updated Issue)
"""
