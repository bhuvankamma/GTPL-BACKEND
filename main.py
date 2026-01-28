from dotenv import load_dotenv
load_dotenv()

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from routes.ticketdashboard import router as ticket_router
from routes.reimbursement import router as reimbursement_router
from routes.empoffboarding import router as offboarding_router


# ==================================================

app = FastAPI(title="HRMS Backend")

# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



    


#ticketdashboard#

app.include_router(ticket_router, tags=["Ticket Dashboard"])
app.include_router(reimbursement_router, tags=["Reimbursement"])
app.include_router(offboarding_router,tags=["Offboarding"])



