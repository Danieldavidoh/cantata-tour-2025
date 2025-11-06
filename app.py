# === 조용한 눈 내리는 효과 ===
silent_snow = """
<style>
.silent-snowflake {
    position: fixed;
    top: -10px;
    color: rgba(255, 255, 255, 0.65);
    font-size: 1em;
    pointer-events: none;
    z-index: 0;
    user-select: none;
    animation: fall_slow linear forwards;
}
@keyframes fall_slow {
    0% { transform: translateY(0px) translateX(0px); opacity: 0.9; }
    100% { transform: translateY(100vh) translateX(20px); opacity: 0.2; }
}
</style>

<script>
function createSilentSnowflake() {
    const snow = document.createElement('div');
    snow.classList.add('silent-snowflake');
    snow.textContent = ['❅','❆','✻','✼'][Math.floor(Math.random()*4)];
    snow.style.left = Math.random() * 100 + 'vw';
    snow.style.fontSize = (Math.random() * 1.2 + 0.8) + 'em';
    snow.style.animationDuration = (Math.random() * 10 + 15) + 's';
    document.body.appendChild(snow);
    setTimeout(() => snow.remove(), 18000);
}
setInterval(createSilentSnowflake, 600);
</script>
"""
st.markdown(silent_snow, unsafe_allow_html=True)
