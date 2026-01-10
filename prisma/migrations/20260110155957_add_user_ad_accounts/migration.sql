-- AlterTable
ALTER TABLE "FacebookSession" ADD COLUMN     "adAccounts" JSONB,
ADD COLUMN     "selectedAdAccountId" TEXT;
