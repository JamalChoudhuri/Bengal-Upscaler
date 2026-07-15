import io
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from rembg import remove
from PIL import Image

app = FastAPI(
    title="Bengal AI Image Processor - Lightweight",
    description="Render Free Plan-এর জন্য অপ্টিমাইজড ইমেজ প্রসেস এপিআই"
)

# CORS ব্লকিং কাটানোর পারমিশন
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "Bengal AI Server is Running Perfectly!"}

@app.post("/process-image/")
async def process_image(
    file: UploadFile = File(...),         
    bg_color: str = Form("#FFFFFF"),      
    output_format: str = Form("PNG")       
):
    try:
        # ১. ফাইল রিড করা
        image_bytes = await file.read()
        input_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")

        # ২. এআই দিয়ে ব্যাকগ্রাউন্ড রিমুভ করা (rembg - মেমোরি ফ্রেন্ডলি মোড)
        transparent_image = remove(input_image)

        # ৩. সলিড কালার ব্যাকগ্রাউন্ড যোগ করা
        hex_color = bg_color.lstrip('#')
        rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        solid_bg = Image.new("RGBA", transparent_image.size, rgb_color + (255,))
        combined_image = Image.alpha_composite(solid_bg, transparent_image)

        # ৪. লাইটওয়েট এইচডি আপস্কেলিং (Lanczos - মেমোরি ক্র্যাশ করবে না)
        # ছবিটিকে ২ গুণ (2x) বড় এবং ক্রিস্টাল ক্লিয়ার করা হচ্ছে
        width, height = combined_image.size
        upscaled_image = combined_image.resize((width * 2, height * 2), Image.Resampling.LANCZOS)

        # ৫. ফরম্যাট সেটআপ ও সেভ করা
        output_buffer = io.BytesIO()
        format_str = output_format.upper()
        
        if format_str in ["JPEG", "JPG"]:
            final_image = upscaled_image.convert("RGB")
            final_image.save(output_buffer, format="JPEG", quality=95)
            media_type = "image/jpeg"
        else:
            upscaled_image.save(output_buffer, format="PNG")
            media_type = "image/png"
            
        output_buffer.seek(0)
        return StreamingResponse(output_buffer, media_type=media_type)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
