-- CreateTable
CREATE TABLE "FacebookSession" (
    "id" TEXT NOT NULL,
    "user_id" TEXT,
    "fb_user_id" TEXT NOT NULL,
    "fb_user_name" TEXT NOT NULL,
    "access_token" TEXT NOT NULL,
    "pages" JSONB NOT NULL,
    "expires_at" TIMESTAMP(3) NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "FacebookSession_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "FacebookSession_id_idx" ON "FacebookSession"("id");
