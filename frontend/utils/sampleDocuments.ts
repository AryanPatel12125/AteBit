// Sample document generator for testing purposes

export interface SampleDocument {
  name: string;
  content: string;
  type: string;
  description: string;
}

export const sampleDocuments: SampleDocument[] = [
  {
    name: 'rental_agreement.txt',
    type: 'text/plain',
    description: 'Sample rental agreement with common clauses',
    content: `RENTAL AGREEMENT

This rental agreement is entered into between John Doe (Tenant) and Jane Smith (Landlord).

PROPERTY DETAILS:
Address: 123 Main Street, Apartment 4B, Anytown, CA 90210
Type: 2-bedroom apartment
Square footage: 850 sq ft

TERMS AND CONDITIONS:

1. RENT: The monthly rent is $2,400, due on the 1st of each month. Late fees of $50 will be charged for payments received after the 5th.

2. SECURITY DEPOSIT: A security deposit of $2,400 is required and will be refunded at the end of the lease term if there are no damages beyond normal wear and tear.

3. LEASE TERM: This lease is for a period of 12 months, beginning January 1, 2024, and ending December 31, 2024.

4. PETS: No pets are allowed on the premises without written consent from the landlord. If approved, an additional pet deposit of $500 is required.

5. MAINTENANCE: The tenant is responsible for basic maintenance and cleanliness. The landlord will handle major repairs and appliance maintenance.

6. UTILITIES: Tenant is responsible for electricity, gas, internet, and cable. Landlord covers water, sewer, and trash collection.

7. TERMINATION: Either party may terminate this agreement with 30 days written notice. Early termination by tenant forfeits security deposit.

8. ENTRY: The landlord may enter the premises for inspections with 24 hours notice, except in emergencies.

9. SUBLETTING: Subletting is not permitted without written consent from the landlord.

10. SMOKING: Smoking is prohibited inside the apartment and common areas.

This agreement is governed by the laws of the State of California.

Signed:
John Doe (Tenant) - Date: January 1, 2024
Jane Smith (Landlord) - Date: January 1, 2024

Contact Information:
Landlord: jane.smith@email.com, (555) 123-4567
Property Management: ABC Property Management, (555) 987-6543`
  },
  {
    name: 'employment_contract.txt',
    type: 'text/plain',
    description: 'Employment contract with various clauses',
    content: `EMPLOYMENT AGREEMENT

This Employment Agreement is entered into between TechCorp Inc. (Company) and Sarah Johnson (Employee).

POSITION AND DUTIES:
Position: Senior Software Engineer
Department: Engineering
Start Date: March 1, 2024
Reports to: Engineering Manager

COMPENSATION AND BENEFITS:

1. SALARY: Annual salary of $120,000, paid bi-weekly.

2. BENEFITS: Employee is eligible for health insurance, dental insurance, 401(k) with company match, and 15 days paid vacation per year.

3. STOCK OPTIONS: Employee will receive 1,000 stock options vesting over 4 years.

TERMS AND CONDITIONS:

4. WORK SCHEDULE: Standard work week is 40 hours, Monday through Friday, 9 AM to 5 PM.

5. REMOTE WORK: Employee may work remotely up to 2 days per week with manager approval.

6. CONFIDENTIALITY: Employee agrees to maintain confidentiality of all proprietary information and trade secrets.

7. NON-COMPETE: Employee agrees not to work for direct competitors for 12 months after termination.

8. INTELLECTUAL PROPERTY: All work products created during employment belong to the Company.

9. TERMINATION: Employment may be terminated by either party with 2 weeks notice. Company may terminate immediately for cause.

10. SEVERANCE: If terminated without cause, employee will receive 4 weeks severance pay.

11. DISPUTE RESOLUTION: Any disputes will be resolved through binding arbitration.

This agreement is governed by the laws of the State of Delaware.

Signed:
Sarah Johnson (Employee) - Date: February 15, 2024
Michael Chen, HR Director (Company) - Date: February 15, 2024

Company Contact:
TechCorp Inc.
456 Innovation Drive
San Francisco, CA 94105
hr@techcorp.com`
  },
  {
    name: 'service_agreement.txt',
    type: 'text/plain',
    description: 'Service agreement with payment terms',
    content: `SERVICE AGREEMENT

This Service Agreement is entered into between Digital Solutions LLC (Service Provider) and ABC Corporation (Client).

SERVICE DESCRIPTION:
The Service Provider will provide web development and digital marketing services including:
- Website design and development
- Search engine optimization (SEO)
- Social media management
- Monthly analytics reporting

PROJECT DETAILS:

1. SCOPE OF WORK: Complete redesign of client website with modern responsive design, implementation of SEO best practices, and ongoing digital marketing support.

2. TIMELINE: Project completion within 8 weeks from contract signing. Ongoing services to continue monthly thereafter.

3. DELIVERABLES:
   - New website with 10 pages
   - Mobile-responsive design
   - SEO optimization
   - Monthly performance reports
   - Social media content calendar

FINANCIAL TERMS:

4. PROJECT FEE: One-time development fee of $15,000 due in three installments:
   - $5,000 upon contract signing
   - $5,000 at 50% completion
   - $5,000 upon final delivery

5. MONTHLY RETAINER: $2,500 per month for ongoing services, due on the 1st of each month.

6. ADDITIONAL WORK: Any work outside the agreed scope will be billed at $150 per hour.

7. PAYMENT TERMS: Net 30 days. Late payments subject to 1.5% monthly interest charge.

TERMS AND CONDITIONS:

8. INTELLECTUAL PROPERTY: Client retains ownership of all content provided. Service Provider retains rights to development methodologies and tools.

9. CONFIDENTIALITY: Both parties agree to maintain confidentiality of proprietary information.

10. LIABILITY: Service Provider's liability is limited to the amount paid under this agreement.

11. TERMINATION: Either party may terminate with 30 days written notice. Client responsible for payment of completed work.

12. FORCE MAJEURE: Neither party liable for delays due to circumstances beyond reasonable control.

This agreement is governed by the laws of the State of New York.

Signed:
Robert Martinez, CEO - ABC Corporation - Date: January 20, 2024
Lisa Wong, Managing Director - Digital Solutions LLC - Date: January 20, 2024`
  },
  {
    name: 'nda_agreement.txt',
    type: 'text/plain',
    description: 'Non-disclosure agreement with strict confidentiality terms',
    content: `NON-DISCLOSURE AGREEMENT (NDA)

This Non-Disclosure Agreement is entered into between InnovateTech Corp. (Disclosing Party) and Alex Thompson (Receiving Party).

PURPOSE: The parties wish to explore a potential business relationship involving the disclosure of confidential information.

CONFIDENTIAL INFORMATION DEFINITION:

1. SCOPE: Confidential Information includes all technical data, trade secrets, know-how, research, product plans, products, services, customers, customer lists, markets, software, developments, inventions, processes, formulas, technology, designs, drawings, engineering, hardware configuration information, marketing, finances, or other business information.

2. EXCLUSIONS: Information that is:
   - Already known to the public
   - Independently developed without use of confidential information
   - Rightfully received from third parties
   - Required to be disclosed by law

OBLIGATIONS:

3. NON-DISCLOSURE: Receiving Party agrees not to disclose any Confidential Information to third parties without written consent.

4. NON-USE: Receiving Party will not use Confidential Information for any purpose other than evaluating the potential business relationship.

5. PROTECTION: Receiving Party will protect Confidential Information with the same degree of care used for its own confidential information, but not less than reasonable care.

6. RETURN OF INFORMATION: Upon request, all Confidential Information and copies must be returned or destroyed.

TERMS:

7. DURATION: This agreement remains in effect for 5 years from the date of signing.

8. REMEDIES: Breach of this agreement may cause irreparable harm, entitling the Disclosing Party to seek injunctive relief and monetary damages.

9. NO LICENSE: No license or rights are granted except as expressly stated herein.

10. SURVIVAL: Obligations survive termination of any business relationship.

11. GOVERNING LAW: This agreement is governed by the laws of the State of California.

12. ENTIRE AGREEMENT: This constitutes the entire agreement regarding confidentiality.

Signed:
Alex Thompson (Receiving Party) - Date: February 10, 2024
Dr. Patricia Kim, CTO - InnovateTech Corp. (Disclosing Party) - Date: February 10, 2024

Witness:
Jennifer Adams, Legal Counsel - Date: February 10, 2024`
  }
];

export function generateSampleFile(document: SampleDocument): File {
  return new File([document.content], document.name, { type: document.type });
}

export function createPDFContent(textContent: string): string {
  // Simple PDF structure for testing
  return `%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length ${textContent.length + 50}
>>
stream
BT
/F1 12 Tf
50 750 Td
${textContent.split('\n').map((line, i) => `(${line}) Tj 0 -15 Td`).join('\n')}
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
${400 + textContent.length}
%%EOF`;
}

export function generateSamplePDF(document: SampleDocument): File {
  const pdfContent = createPDFContent(document.content.substring(0, 500)); // Truncate for PDF
  return new File([pdfContent], document.name.replace('.txt', '.pdf'), { type: 'application/pdf' });
}