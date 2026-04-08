图 3.6 地面点提取与平面拟合效果图素材
处理流程参考 /home/scy/catkin_ws_hdl_location/src/hdl_localization-master/scripts/floor_detection_nodelet.cpp

文件说明：
01_raw_scene.ply               原始点云
02_ground_candidates.ply       候选地面点高亮结果
03_ground_plane_inliers.ply    RANSAC 地面内点高亮结果
01_raw_scene.png               原始点云独立图片
01_raw_scene.pdf               原始点云矢量版图片
02_ground_candidates.png       候选地面点独立图片
02_ground_candidates.pdf       候选地面点矢量版图片
03_ground_plane_inliers.png    RANSAC 平面拟合独立图片
03_ground_plane_inliers.pdf    RANSAC 平面拟合矢量版图片
00_ground_extraction_pipeline.png  三联流程图图片
00_ground_extraction_pipeline.pdf  三联流程图矢量版图片

若需要手动截图：
1. 用 Open3D / CloudCompare 打开上述 ply 文件。
2. 建议白底、透视视图，保持三个视角一致。
3. 截图顺序依次为原始点云、候选地面点、RANSAC 平面拟合。
4. 颜色建议保持灰色点云、绿色地面点、蓝色拟合平面。

若需要手动调图，优先调整以下参数：
1. view_init(elev, azim)：控制三维视角。
2. scatter 的 s 和 alpha：控制点大小与透明度。
3. z_low / z_high：控制候选地面点高度范围。
4. normal_filter_thresh_deg：控制法向筛选强度。
5. ransac_dist：控制平面拟合内点距离阈值。
6. mins / maxs：控制坐标轴显示范围。